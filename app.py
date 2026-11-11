"""Champion Restoration & Construction — Transactions, v1.
Run: streamlit run app.py
"""
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import streamlit as st

from db import DB_PATH, init_db, get_transactions, get_statuses, add_transaction, update_transaction, delete_transaction, set_status
from schedule import FREQUENCIES, build_occurrences

st.set_page_config(page_title='Champion | Transactions', page_icon='💵', layout='wide')
init_db()

st.markdown('''<style>
.block-container {max-width: 1220px; padding-top: 2rem}
[data-testid="stMetric"] {background: #f5f7fa; border: 1px solid #e6e9ee; border-radius: 12px; padding: 14px}
</style>''', unsafe_allow_html=True)
st.title('Champion · Transactions')
st.caption('Phase 1 — Enter payments and deposits, schedule repeating transactions, and track each due date individually.')


def amount_to_cents(value):
    try:
        cents = int((Decimal(str(value)) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError):
        return None
    return cents if cents > 0 else None


def money(cents):
    return f'${cents / 100:,.2f}'


def validate(name, amount):
    if not name.strip():
        return 'Please enter a transaction name.'
    if amount_to_cents(amount) is None:
        return 'Amount must be greater than $0.'
    return None


add_tab, schedule_tab, manage_tab = st.tabs(['➕ Add transaction', '📅 Scheduled transactions', '⚙️ Edit / delete'])

with add_tab:
    st.subheader('Add a payment or expected deposit')
    with st.form('add_form', clear_on_submit=True):
        name = st.text_input('Transaction name *', placeholder='Example: Office rent, Five Star Pro payment, Insurance deposit')
        c1, c2 = st.columns(2)
        with c1:
            kind = st.selectbox('Transaction type *', ['Expense', 'Deposit'])
            amount = st.number_input('Amount ($) *', min_value=0.00, value=0.00, step=50.00, format='%.2f')
        with c2:
            due_date = st.date_input('First due / expected date *', value=date.today())
            frequency = st.selectbox('Repeats', FREQUENCIES, index=0)
        notes = st.text_area('Notes (optional)', placeholder='Invoice, project, vendor, or other details', height=85)
        submitted = st.form_submit_button('Save transaction', type='primary', use_container_width=True)
        if submitted:
            error = validate(name, amount)
            if error:
                st.error(error)
            else:
                add_transaction(name.strip(), kind, amount_to_cents(amount), due_date.isoformat(), frequency, notes.strip())
                st.success('Transaction saved to your local SQLite database.')
    st.info('Recurring items are scheduled automatically. Marking one occurrence paid does not mark future occurrences paid.')

with schedule_tab:
    st.subheader('Payment and deposit schedule')
    today = date.today()
    preset = st.radio('Show dates', ['Next 30 days', 'This month', 'Next 90 days', 'Custom range'], horizontal=True)
    if preset == 'This month':
        start = today.replace(day=1)
        from calendar import monthrange
        end = today.replace(day=monthrange(today.year,today.month)[1])
    elif preset == 'Next 90 days':
        start, end = today, today + timedelta(days=90)
    elif preset == 'Custom range':
        cc1, cc2 = st.columns(2)
        with cc1:
            start = st.date_input('From', value=today - timedelta(days=30), key='from')
        with cc2:
            end = st.date_input('Through', value=today + timedelta(days=60), key='through')
    else:
        start, end = today, today + timedelta(days=30)
    if start > end:
        st.error('The start date must not be after the end date.')
    elif (end - start).days > 366 * 3:
        st.warning('Choose a range of three years or less to keep the table manageable.')
    else:
        txs = get_transactions()
        states = get_statuses()
        rows = build_occurrences(txs, states, start, end)
        unpaid_out = sum(r['amount_cents'] for r in rows if r['kind'] == 'Expense' and not r['paid'])
        unpaid_in = sum(r['amount_cents'] for r in rows if r['kind'] == 'Deposit' and not r['paid'])
        completed = sum(1 for r in rows if r['paid'])
        m1, m2, m3 = st.columns(3)
        m1.metric('Outstanding expenses', money(unpaid_out))
        m2.metric('Expected deposits', money(unpaid_in))
        m3.metric('Paid / received', f'{completed} of {len(rows)}')
        st.caption('Balances shown are only transactions in the selected dates. Bank balances and forecasts come in a later phase.')
        filter_kind = st.selectbox('Filter', ['All', 'Expenses only', 'Deposits only', 'Unpaid / not received'])
        if filter_kind == 'Expenses only':
            rows = [r for r in rows if r['kind'] == 'Expense']
        elif filter_kind == 'Deposits only':
            rows = [r for r in rows if r['kind'] == 'Deposit']
        elif filter_kind == 'Unpaid / not received':
            rows = [r for r in rows if not r['paid']]
        if not rows:
            st.info('No scheduled transactions match this range/filter. Add one in the first tab.')
        else:
            if len(rows) > 200:
                st.warning(f'Showing first 200 of {len(rows)} occurrences. Use a narrower range to see all of them.')
                rows = rows[:200]
            head = st.columns([1.3, 2.7, 1, 1, 1.25, 1.7])
            for col, title in zip(head, ['Due date', 'Transaction', 'Type', 'Amount', 'Frequency', 'Status / action']):
                col.markdown(f'**{title}**')
            for r in rows:
                cols = st.columns([1.3, 2.7, 1, 1, 1.25, 1.7], vertical_alignment='center')
                cols[0].write(r['occurrence_date'])
                cols[1].write(r['name'])
                cols[2].write(r['kind'])
                cols[3].write(money(r['amount_cents']))
                cols[4].write(r['frequency'])
                label = ('↩ Mark unpaid' if r['kind'] == 'Expense' else '↩ Not received') if r['paid'] else ('✓ Mark paid' if r['kind'] == 'Expense' else '✓ Received')
                if cols[5].button(label, key=f"status-{r['id']}-{r['occurrence_date']}", use_container_width=True):
                    set_status(r['id'], r['occurrence_date'], not r['paid'])
                    st.rerun()
                st.divider()

with manage_tab:
    st.subheader('Edit or delete a transaction')
    txs = get_transactions()
    if not txs:
        st.info('No transactions yet.')
    else:
        choices = {f"#{t['id']} · {t['name']} ({t['kind']}, {money(t['amount_cents'])})":t for t in txs}
        selected_label = st.selectbox('Choose a saved transaction', list(choices))
        selected = choices[selected_label]
        with st.form(f"edit-{selected['id']}"):
            edit_name = st.text_input('Name', value=selected['name'])
            c1, c2 = st.columns(2)
            with c1:
                edit_kind = st.selectbox('Type', ['Expense','Deposit'], index=['Expense','Deposit'].index(selected['kind']))
                edit_amount = st.number_input('Amount ($)', min_value=0.00, value=selected['amount_cents']/100, format='%.2f')
            with c2:
                edit_due = st.date_input('First due date', value=date.fromisoformat(selected['due_date']))
                edit_freq = st.selectbox('Frequency', FREQUENCIES, index=FREQUENCIES.index(selected['frequency']))
            edit_notes = st.text_area('Notes', value=selected['notes'])
            if st.form_submit_button('Save changes', type='primary'):
                error = validate(edit_name, edit_amount)
                if error:
                    st.error(error)
                else:
                    update_transaction(selected['id'], edit_name.strip(), edit_kind, amount_to_cents(edit_amount), edit_due.isoformat(), edit_freq, edit_notes.strip())
                    st.success('Saved changes. Past status records are retained for dates still on this schedule.')
                    st.rerun()
        with st.expander('Delete this transaction'):
            st.warning('Deleting this transaction also deletes its paid/received history. This cannot be undone.')
            confirm = st.checkbox('I understand this will permanently delete the transaction and its history', key=f"confirm-{selected['id']}")
            if st.button('Delete transaction', disabled=not confirm, key=f"delete-{selected['id']}"):
                delete_transaction(selected['id'])
                st.rerun()

st.divider()
st.caption(f'Local database: {DB_PATH} · Stored only on this computer. Make periodic backup copies of the data/champion.db file while the app is closed.')
