"""
Run this script once to seed all payment methods into the database.
Place it anywhere and run:  python manage.py shell < seed.py
Or paste into the Django shell.
"""

import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')  # update this

from .core.models import PaymentMethod 

PaymentMethod.objects.all().delete()  # clear existing if re-running

methods = [
    # ── Bitcoin ───────────────────────────────────────────────────────────────
    dict(
        name='Bitcoin',          ticker='BTC',
        network_label='BTC Network',     network_key='btc',
        address='bc1qssf8qnsnq7k77cpevx4yc3r04s48ean0prnuf3',
        color='bg-orange-500',   icon_symbol='₿',   sort_order=1,
    ),

    # ── Ethereum ──────────────────────────────────────────────────────────────
    dict(
        name='Ethereum',         ticker='ETH',
        network_label='ERC-20 Network',  network_key='eth',
        address='0xa5338C31B98843Cfe2438A3eF731d15d2F7DaBE0',
        color='bg-blue-600',     icon_symbol='Ξ',   sort_order=2,
    ),

    # ── USDT ─ 4 networks ─────────────────────────────────────────────────────
    dict(
        name='USDT (TRC-20)',    ticker='USDT',
        network_label='Tron TRC-20',     network_key='trx',
        address='TREfbXuqh1UktAJ5neivC36qzuKKRZMbur',
        color='bg-green-500',    icon_symbol='₮',   sort_order=3,
    ),
    dict(
        name='USDT (ERC-20)',    ticker='USDT',
        network_label='Ethereum ERC-20', network_key='eth',
        address='0xa5338C31B98843Cfe2438A3eF731d15d2F7DaBE0',
        color='bg-green-500',    icon_symbol='₮',   sort_order=4,
    ),
    dict(
        name='USDT (BEP-20)',    ticker='USDT',
        network_label='BNB Smart Chain BEP-20', network_key='bnb',
        address='0xa5338C31B98843Cfe2438A3eF731d15d2F7DaBE0',
        color='bg-green-500',    icon_symbol='₮',   sort_order=5,
    ),
    dict(
        name='USDT (SOL)',       ticker='USDT',
        network_label='Solana Network',  network_key='sol',
        address='HmxaeEmoxPJGRCFGKVLp8aVjHsS1Q32RhZnhwYgdEcP',
        color='bg-green-500',    icon_symbol='₮',   sort_order=6,
    ),

    # ── USDC ─ 3 networks ─────────────────────────────────────────────────────
    dict(
        name='USDC (ERC-20)',    ticker='USDC',
        network_label='Ethereum ERC-20', network_key='eth',
        address='0xa5338C31B98843Cfe2438A3eF731d15d2F7DaBE0',
        color='bg-blue-400',     icon_symbol='$',   sort_order=7,
    ),
    dict(
        name='USDC (BEP-20)',    ticker='USDC',
        network_label='BNB Smart Chain BEP-20', network_key='bnb',
        address='0xa5338C31B98843Cfe2438A3eF731d15d2F7DaBE0',
        color='bg-blue-400',     icon_symbol='$',   sort_order=8,
    ),
    dict(
        name='USDC (SOL)',       ticker='USDC',
        network_label='Solana Network',  network_key='sol',
        address='HmxaeEmoxPJGRCFGKVLp8aVjHsS1Q32RhZnhwYgdEcP',
        color='bg-blue-400',     icon_symbol='$',   sort_order=9,
    ),

    # ── Tron TRX ──────────────────────────────────────────────────────────────
    dict(
        name='Tron',             ticker='TRX',
        network_label='TRC-20 Network',  network_key='trx',
        address='TREfbXuqh1UktAJ5neivC36qzuKKRZMbur',
        color='bg-red-500',      icon_symbol='T',   sort_order=10,
    ),

    # ── BNB ───────────────────────────────────────────────────────────────────
    dict(
        name='BNB',              ticker='BNB',
        network_label='BNB Smart Chain BEP-20', network_key='bnb',
        address='0xa5338C31B98843Cfe2438A3eF731d15d2F7DaBE0',
        color='bg-yellow-400',   icon_symbol='B',   sort_order=11,
    ),

    # ── Solana ────────────────────────────────────────────────────────────────
    dict(
        name='Solana',           ticker='SOL',
        network_label='Solana Network',  network_key='sol',
        address='HmxaeEmoxPJGRCFGKVLp8aVjHsS1Q32RhZnhwYgdEcP',
        color='bg-purple-500',   icon_symbol='◎',   sort_order=12,
    ),

    # ── Dogecoin ──────────────────────────────────────────────────────────────
    dict(
        name='Dogecoin',         ticker='DOGE',
        network_label='Dogecoin Network', network_key='doge',
        address='DGZzQ2x5S1BwFmu44iDGuXHf96UNe1ndKV',
        color='bg-yellow-500',   icon_symbol='Ð',   sort_order=13,
    ),

    # ── Litecoin ──────────────────────────────────────────────────────────────
    dict(
        name='Litecoin',         ticker='LTC',
        network_label='LTC Network',     network_key='ltc',
        address='ltc1qztgylrvy3qdclqjwrsc4fzj2ve76wfdnvuqdy0',
        color='bg-gray-500',     icon_symbol='Ł',   sort_order=14,
    ),
]

created = 0
for m in methods:
    PaymentMethod.objects.create(**m)
    created += 1

print(f'✅ Created {created} payment methods.')