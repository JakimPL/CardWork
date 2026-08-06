from collections.abc import Mapping
from struct import pack, unpack_from
from typing import Final

EXECUTABLE: Final[bytes] = b"MZ"
PORTABLE: Final[bytes] = b"PE\x00\x00"
SIGNATURE: Final[int] = 0x3C

HEADER_LENGTHS: Final[int] = 0x14
SECTION_TABLE: Final[int] = 0x18
SECTION_COUNT: Final[int] = 0x06
SECTION_LENGTH: Final[int] = 0x28
SECTION_NAME: Final[int] = 0x08
SECTION_ADDRESS: Final[int] = 0x0C
SECTION_OFFSET: Final[int] = 0x14
RESOURCE_SECTION: Final[bytes] = b".rsrc"

DIRECTORY_NAMED: Final[int] = 0x0C
DIRECTORY_NUMBERED: Final[int] = 0x0E
DIRECTORY_ENTRIES: Final[int] = 0x10
ENTRY_LENGTH: Final[int] = 0x08
ENTRY_OFFSET: Final[int] = 0x04
SUBDIRECTORY: Final[int] = 1 << 31

BITMAP_TYPE: Final[int] = 0x02
DATA_LENGTH: Final[int] = 0x04

CORE_HEADER: Final[int] = 0x0C
INFO_HEADER: Final[int] = 0x28
CORE_DEPTH: Final[int] = 0x0A
CORE_ENTRY: Final[int] = 0x03
INFO_DEPTH: Final[int] = 0x0E
INFO_PALETTE: Final[int] = 0x20
INFO_ENTRY: Final[int] = 0x04
FILE_HEADER: Final[int] = 0x0E
PALETTED: Final[int] = 16


def word(image: bytes, offset: int) -> int:
    """The unsigned sixteen-bit number standing at one offset of an image."""
    return int(unpack_from("<H", image, offset)[0])


def double_word(image: bytes, offset: int) -> int:
    """The unsigned thirty-two-bit number standing at one offset of an image."""
    return int(unpack_from("<I", image, offset)[0])


def headers(image: bytes) -> int:
    """Where the headers of one portable executable begin, read out of the stub standing ahead of them.

    Raises:
        ValueError: when the image opens as something other than a portable executable.
    """
    if not image.startswith(EXECUTABLE):
        raise ValueError(f"An executable opens with {EXECUTABLE!r}, and this one opens with {image[:2]!r}")

    offset = double_word(image, SIGNATURE)
    marked = image[offset : offset + len(PORTABLE)]
    if marked != PORTABLE:
        raise ValueError(f"A portable executable is marked {PORTABLE!r}, and this one is marked {marked!r}")

    return offset


def resources(image: bytes) -> tuple[int, int]:
    """Where the resources of one executable stand: their offset in the file, and the address they load at.

    A resource names its data by the address it holds once the image is loaded, so reading one off the file
    takes both numbers: the difference between them is what turns an address back into an offset.

    Raises:
        ValueError: when the image carries no resource section.
    """
    offset = headers(image)
    sections = offset + SECTION_TABLE + word(image, offset + HEADER_LENGTHS)
    for index in range(word(image, offset + SECTION_COUNT)):
        header = sections + SECTION_LENGTH * index
        if image[header : header + SECTION_NAME].rstrip(b"\x00") == RESOURCE_SECTION:
            return double_word(image, header + SECTION_OFFSET), double_word(image, header + SECTION_ADDRESS)

    raise ValueError(f"An image holding resources carries a {RESOURCE_SECTION!r} section, and this one holds none")


def entries(image: bytes, directory: int) -> tuple[tuple[int, int], ...]:
    """The identifier and offset of each entry of one resource directory, taking the entries named by number.

    An entry offset stands from the head of the resource section, and carries its high bit set where it leads
    to a directory of its own rather than to the data itself.
    """
    first = directory + DIRECTORY_ENTRIES + ENTRY_LENGTH * word(image, directory + DIRECTORY_NAMED)
    return tuple(
        (
            double_word(image, first + ENTRY_LENGTH * index),
            double_word(image, first + ENTRY_LENGTH * index + ENTRY_OFFSET),
        )
        for index in range(word(image, directory + DIRECTORY_NUMBERED))
    )


def data(image: bytes, section: int, offset: int) -> int | None:
    """Where one entry of a resource directory bottoms out, following it down to the first language it holds."""
    if not offset & SUBDIRECTORY:
        return section + offset

    directory = section + (offset & ~SUBDIRECTORY)
    for _, below in entries(image, directory):
        return data(image, section, below)

    return None


def bitmaps(image: bytes) -> Mapping[int, bytes]:
    """Every bitmap of one executable as a BMP file, addressed by the identifier it is held under.

    Raises:
        ValueError: when the image holds no bitmaps at all.
    """
    section, address = resources(image)
    for kind, offset in entries(image, section):
        if kind == BITMAP_TYPE and offset & SUBDIRECTORY:
            return held(image, section, address, section + (offset & ~SUBDIRECTORY))

    raise ValueError("An image holding card artwork carries bitmap resources, and this one holds none")


def held(image: bytes, section: int, address: int, directory: int) -> Mapping[int, bytes]:
    """Each bitmap one directory holds, as a file a reader opens, under the identifier it stands at."""
    found: dict[int, bytes] = {}
    for identifier, offset in entries(image, directory):
        entry = data(image, section, offset)
        if entry is None:
            continue

        start = double_word(image, entry) - (address - section)
        length = double_word(image, entry + DATA_LENGTH)
        found[identifier] = bitmap_file(image[start : start + length])

    return found


def bitmap_file(bitmap: bytes) -> bytes:
    """One device-independent bitmap under the fourteen-byte header that makes it a file a reader opens.

    A resource holds a bitmap from its own header onwards, so the pixels stand wherever the header and the
    palette ahead of them end — which is the one number a file header states and a resource leaves out.

    Raises:
        ValueError: when the bitmap opens with a header of a shape no pixels are read from.
    """
    header = double_word(bitmap, 0)
    if header == CORE_HEADER:
        pixels = FILE_HEADER + header + CORE_ENTRY * palette(word(bitmap, CORE_DEPTH), 0)
    elif header == INFO_HEADER:
        stated = double_word(bitmap, INFO_PALETTE)
        pixels = FILE_HEADER + header + INFO_ENTRY * palette(word(bitmap, INFO_DEPTH), stated)
    else:
        raise ValueError(f"A bitmap header runs {CORE_HEADER} or {INFO_HEADER} bytes, and this one runs {header}")

    return pack("<2sIHHI", b"BM", FILE_HEADER + len(bitmap), 0, 0, pixels) + bitmap


def palette(depth: int, stated: int) -> int:
    """How many colours one bitmap carries ahead of its pixels, at the depth it draws them at.

    A bitmap drawing few enough colours to name them holds one entry per value a pixel takes, and states a
    count of its own only where it holds fewer than that.
    """
    if depth >= PALETTED:
        return 0

    return stated if stated else 1 << depth
