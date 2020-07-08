from ubinascii import hexlify

from trezor import ui
from trezor.messages import ButtonRequestType, CardanoAddressType
from trezor.strings import format_amount
from trezor.ui.button import ButtonDefault
from trezor.ui.scroll import Paginated
from trezor.ui.text import Text
from trezor.utils import chunks

from apps.common.confirm import confirm, require_confirm, require_hold_to_confirm
from apps.common.layout import show_warning

from ..helpers import protocol_magics

if False:
    from typing import List
    from trezor import wire
    from trezor.messages import CardanoBlockchainPointerType


def format_coin_amount(amount: int) -> str:
    return "%s %s" % (format_amount(amount, 6), "ADA")


async def confirm_sending(ctx: wire.Context, amount: int, to: str):
    t1 = Text("Confirm transaction", ui.ICON_SEND, ui.GREEN)
    t1.normal("Confirm sending:")
    t1.bold(format_coin_amount(amount))
    t1.normal("to:")

    to_lines = list(chunks(to, 17))
    t1.bold(to_lines[0])

    pages = [t1] + _paginate_lines(to_lines, 1, "Confirm transaction", ui.ICON_SEND)

    await require_confirm(ctx, Paginated(pages))


async def confirm_transaction(ctx, amount: int, fee: int, protocol_magic: int):
    t1 = Text("Confirm transaction", ui.ICON_SEND, ui.GREEN)
    t1.normal("Total amount:")
    t1.bold(format_coin_amount(amount))
    t1.normal("including fee:")
    t1.bold(format_coin_amount(fee))

    t2 = Text("Confirm transaction", ui.ICON_SEND, ui.GREEN)
    t2.normal("Network:")
    t2.bold(protocol_magics.to_ui_string(protocol_magic))

    await require_hold_to_confirm(ctx, Paginated([t1, t2]))


async def show_address(
    ctx: wire.Context,
    address: str,
    address_type: CardanoAddressType,
    path: List[int],
    network: int = None,
) -> bool:
    """
    Custom show_address function is needed because cardano addresses don't
    fit on a single screen.
    """
    path_str = address_n_to_str(path)
    t1 = Text(path_str, ui.ICON_RECEIVE, ui.GREEN)
    if network is not None:
        t1.normal("%s network" % protocol_magics.to_ui_string(network))
    t1.normal("%s address" % _format_address_type(address_type))

    address_lines = list(chunks(address, 17))
    t1.bold(address_lines[0])
    t1.bold(address_lines[1])
    t1.bold(address_lines[2])

    pages = [t1] + _paginate_lines(address_lines, 3, path_str, ui.ICON_RECEIVE)

    return await confirm(
        ctx,
        Paginated(pages),
        code=ButtonRequestType.Address,
        cancel="QR",
        cancel_style=ButtonDefault,
    )


def _format_address_type(address_type: CardanoAddressType) -> str:
    if address_type == CardanoAddressType.BYRON:
        return "Legacy"
    elif address_type == CardanoAddressType.BASE:
        return "Base"
    elif address_type == CardanoAddressType.POINTER:
        return "Pointer"
    elif address_type == CardanoAddressType.ENTERPRISE:
        return "Enterprise"
    elif address_type == CardanoAddressType.REWARD:
        return "Reward"
    else:
        raise ValueError("Unknown address type")


def _paginate_lines(
    lines: List[str], offset: int, desc: str, icon: str, per_page: int = 4
) -> List[ui.Component]:
    pages = []
    if len(lines) > offset:
        to_pages = list(chunks(lines[offset:], per_page))
        for page in to_pages:
            t = Text(desc, icon, ui.GREEN)
            for line in page:
                t.bold(line)
            pages.append(t)

    return pages


async def show_warning_address_foreign_staking_key(
    ctx: wire.Context,
    spending_account_path: List[int],
    staking_account_path: List[int],
    staking_key_hash: bytes,
) -> None:
    await show_warning(
        ctx,
        (
            "Stake rights associated",
            "with this address do",
            "not belong to your",
            "account",
            address_n_to_str(spending_account_path),
        ),
        button="Ok",
    )

    if staking_account_path:
        staking_key_message = (
            "Stake account path:",
            address_n_to_str(staking_account_path),
        )
    else:
        staking_key_message = ("Staking key:", hexlify(staking_key_hash))

    await show_warning(
        ctx, staking_key_message, button="Ok",
    )


async def show_warning_address_pointer(
    ctx: wire.Context, pointer: CardanoBlockchainPointerType
) -> None:
    await show_warning(
        ctx,
        (
            "Pointer address:",
            "Block: %s" % pointer.block_index,
            "Transaction: %s" % pointer.tx_index,
            "Certificate: %s" % pointer.certificate_index,
        ),
        button="Ok",
    )
