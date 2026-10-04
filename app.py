import json
import re

import streamlit as st
from google import genai
from google.genai import types

from splitter import (
    calculate_equal_split,
    verify_split,
    round_money,
    calculate_quantity_split,
    verify_quantity_split,
    allocate_tax_and_discount,
    verify_final_split,
)

from email_sender import send_split_email


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SplitSnap",
    page_icon="🧾",
    layout="wide"
)

# Keep the app compact so normal receipts fit in a single viewport
# whenever the amount of content allows it.
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 1rem;
        }

        [data-testid="stVerticalBlock"] {
            gap: 0.45rem;
        }

        [data-testid="stHorizontalBlock"] {
            gap: 0.75rem;
        }

        hr {
            margin: 0.45rem 0;
        }

        h1, h2, h3 {
            margin-top: 0.35rem;
            margin-bottom: 0.35rem;
        }

        [data-testid="stCaptionContainer"] {
            margin-bottom: 0.15rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🧾 SplitSnap")
st.caption("AI Receipt & Bill Splitter")


# ============================================================
# GEMINI CLIENT
# ============================================================

try:

    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

    client = genai.Client(
        api_key=GEMINI_API_KEY
    )

except Exception as error:

    st.error(
        "Gemini API key is not configured correctly."
    )

    st.code(
        str(error)
    )

    st.stop()


# ============================================================
# SESSION STATE
# ============================================================

if "receipt" not in st.session_state:
    st.session_state["receipt"] = None

if "receipt_confirmed" not in st.session_state:
    st.session_state["receipt_confirmed"] = False

if "equal_split" not in st.session_state:
    st.session_state["equal_split"] = None

if "quantity_split" not in st.session_state:
    st.session_state["quantity_split"] = None

if "quantity_subtotals" not in st.session_state:
    st.session_state["quantity_subtotals"] = None

if "quantity_assignments" not in st.session_state:
    st.session_state["quantity_assignments"] = None

if "scroll_target" not in st.session_state:
    st.session_state["scroll_target"] = None


# ============================================================
# GEMINI RECEIPT PROMPT
# ============================================================

RECEIPT_PROMPT = """
Analyze this receipt image carefully.

Extract the receipt information and return ONLY valid JSON.

Use exactly this structure:

{
  "merchant": "string",
  "items": [
    {
      "name": "string",
      "quantity": number,
      "unit_price": number,
      "total": number
    }
  ],
  "subtotal": number,
  "tax": number,
  "discount": number or null,
  "total": number
}

Rules:

1. Extract every visible purchased item.
2. Preserve the quantity exactly as shown.
3. Calculate unit_price if it is not explicitly shown.
4. Use the item's actual line total.
5. subtotal should represent the receipt subtotal.
6. tax should represent the TOTAL tax amount.
7. discount should represent the TOTAL discount.
8. If there is no discount, use null.
9. total should represent the final amount actually payable.
10. Do not include currency symbols.
11. Do not include Markdown.
12. Do not include explanations.
13. Return only JSON.
"""


# ============================================================
# JSON CLEANUP
# ============================================================

def clean_json_response(response_text):

    response_text = response_text.strip()

    response_text = re.sub(
        r"^```json\s*",
        "",
        response_text,
        flags=re.IGNORECASE
    )

    response_text = re.sub(
        r"^```\s*",
        "",
        response_text
    )

    response_text = re.sub(
        r"\s*```$",
        "",
        response_text
    )

    return response_text.strip()


def set_scroll_target(target):
    """Set the next section that should be smoothly brought into view."""
    st.session_state["scroll_target"] = target


def smooth_scroll_to_target():
    """Smoothly scroll the main Streamlit page to the requested section."""
    target = st.session_state.get("scroll_target")

    if not target:
        return

    st.html(
        f"""
        <script>
        setTimeout(() => {{
            const parentDoc = window.parent.document;
            const target = parentDoc.getElementById({target!r});

            if (target) {{
                target.scrollIntoView({{
                    behavior: "smooth",
                    block: "start"
                }});
            }}
        }}, 100);
        </script>
        """
    )

    st.session_state["scroll_target"] = None


# ============================================================
# RECEIPT UPLOAD
# ============================================================

st.header("📷 Upload Receipt")

uploaded_file = st.file_uploader(
    "Upload your receipt image",
    type=[
        "jpg",
        "jpeg",
        "png",
        "webp"
    ]
)


# ============================================================
# PROCESS RECEIPT
# ============================================================

if uploaded_file is not None:

    st.image(
        uploaded_file,
        caption="Uploaded Receipt",
        width=320
    )

    if st.button(
        "🔍 Analyze Receipt",
        use_container_width=True
    ):

        try:

            image_bytes = uploaded_file.getvalue()

            with st.spinner(
                "Analyzing receipt with Gemini..."
            ):

                response = client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=[
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type=uploaded_file.type
                        ),
                        RECEIPT_PROMPT
                    ]
                )

            raw_response = response.text

            cleaned_response = clean_json_response(
                raw_response
            )

            receipt_data = json.loads(
                cleaned_response
            )

            st.session_state["receipt"] = receipt_data

            st.session_state[
                "receipt_confirmed"
            ] = False

            # Reset previous split results
            st.session_state[
                "equal_split"
            ] = None

            st.session_state[
                "quantity_split"
            ] = None

            st.session_state[
                "quantity_subtotals"
            ] = None

            st.session_state[
                "quantity_assignments"
            ] = None

            set_scroll_target("review-section")

            st.success(
                "✅ Receipt analyzed successfully!"
            )

        except json.JSONDecodeError:

            st.error(
                "Gemini returned an invalid JSON response."
            )

            st.code(
                raw_response
            )

        except Exception as error:

            st.error(
                "❌ Could not analyze the receipt."
            )

            st.code(
                str(error)
            )


# ============================================================
# RECEIPT REVIEW
# ============================================================

if st.session_state["receipt"] is not None:

    receipt = st.session_state["receipt"]

    st.divider()

    st.markdown('<div id="review-section"></div>', unsafe_allow_html=True)

    st.header("📝 Review Receipt")

    st.caption(
        "Review and edit the extracted values before confirming."
    )


    # ========================================================
    # MERCHANT
    # ========================================================

    merchant = st.text_input(
        "Merchant",
        value=str(
            receipt.get(
                "merchant",
                ""
            )
        )
    )


    # ========================================================
    # ITEMS
    # ========================================================

    st.subheader("🛒 Items")

    items = receipt.get(
        "items",
        []
    )

    edited_items = []


    for index, item in enumerate(items):

        st.caption(f"Item {index + 1}")

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            item_name = st.text_input(
                "Name",
                value=str(
                    item.get(
                        "name",
                        ""
                    )
                ),
                key=f"item_name_{index}"
            )

        with col2:

            quantity = st.number_input(
                "Quantity",
                min_value=1,
                value=int(
                    item.get(
                        "quantity",
                        1
                    )
                ),
                step=1,
                key=f"item_quantity_{index}"
            )

        with col3:

            unit_price = st.number_input(
                "Unit Price",
                min_value=0.0,
                value=float(
                    item.get(
                        "unit_price",
                        0
                    )
                ),
                step=0.01,
                format="%.2f",
                key=f"item_unit_price_{index}"
            )

        with col4:

            item_total = st.number_input(
                "Item Total",
                min_value=0.0,
                value=float(
                    item.get(
                        "total",
                        0
                    )
                ),
                step=0.01,
                format="%.2f",
                key=f"item_total_{index}"
            )

        edited_items.append(
            {
                "name": item_name,
                "quantity": quantity,
                "unit_price": unit_price,
                "total": item_total
            }
        )


    # ========================================================
    # RECEIPT TOTALS
    # ========================================================

    st.subheader("💰 Receipt Totals")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        subtotal = st.number_input(
            "Subtotal",
            min_value=0.0,
            value=float(
                receipt.get(
                    "subtotal",
                    0
                )
            ),
            step=0.01,
            format="%.2f"
        )

    with col2:

        tax = st.number_input(
            "Tax",
            min_value=0.0,
            value=float(
                receipt.get(
                    "tax",
                    0
                )
            ),
            step=0.01,
            format="%.2f"
        )

    with col3:

        discount_default = receipt.get(
            "discount",
            0
        )

        if discount_default is None:
            discount_default = 0

        discount = st.number_input(
            "Discount",
            min_value=0.0,
            value=float(
                discount_default
            ),
            step=0.01,
            format="%.2f"
        )

    with col4:

        final_total = st.number_input(
            "Final Total",
            min_value=0.0,
            value=float(
                receipt.get(
                    "total",
                    0
                )
            ),
            step=0.01,
            format="%.2f"
        )


    # ========================================================
    # CONFIRM RECEIPT
    # ========================================================

    if st.button(
        "✅ Confirm Receipt",
        use_container_width=True
    ):

        confirmed_receipt = {
            "merchant": merchant,
            "items": edited_items,
            "subtotal": subtotal,
            "tax": tax,
            "discount": discount,
            "total": final_total
        }

        st.session_state[
            "receipt"
        ] = confirmed_receipt

        st.session_state[
            "receipt_confirmed"
        ] = True

        # Reset split results
        st.session_state[
            "equal_split"
        ] = None

        st.session_state[
            "quantity_split"
        ] = None

        st.session_state[
            "quantity_subtotals"
        ] = None

        st.session_state[
            "quantity_assignments"
        ] = None

        set_scroll_target("split-section")

        st.success(
            "✅ Receipt confirmed!"
        )

        st.rerun()


# ============================================================
# SPLITTING SECTION
# ============================================================

if (
    st.session_state["receipt_confirmed"]
    and st.session_state["receipt"] is not None
):

    confirmed_receipt = st.session_state[
        "receipt"
    ]

    st.divider()

    st.markdown('<div id="split-section"></div>', unsafe_allow_html=True)

    st.header("💸 Split Bill")

    st.write(
        f"**Merchant:** "
        f"{confirmed_receipt.get('merchant', 'Unknown')}"
    )

    st.write(
        f"**Final Receipt Total:** "
        f"₹{float(confirmed_receipt.get('total', 0)):.2f}"
    )


    # ========================================================
    # NUMBER OF PEOPLE
    # ========================================================

    number_of_people = st.number_input(
        "Number of People",
        min_value=1,
        max_value=20,
        value=2,
        step=1
    )


    # ========================================================
    # PERSON NAMES
    # ========================================================

    st.subheader("👥 People")

    people = []

    for index in range(
        number_of_people
    ):

        person_name = st.text_input(
            f"Person {index + 1}",
            value=f"Person {index + 1}",
            key=f"person_name_{index}"
        )

        people.append(
            person_name.strip()
            if person_name.strip()
            else f"Person {index + 1}"
        )


    # ========================================================
    # SPLIT METHOD
    # ========================================================

    split_method = st.radio(
        "Choose Split Method",
        [
            "Equal Split",
            "Item-Based Split"
        ],
        horizontal=True
    )


    # ========================================================
    # EQUAL SPLIT
    # ========================================================

    if split_method == "Equal Split":

        st.subheader(
            "⚖️ Equal Split"
        )

        if st.button(
            "🧮 Calculate Equal Split",
            use_container_width=True
        ):

            try:

                total = confirmed_receipt.get(
                    "total",
                    0
                )

                shares = calculate_equal_split(
                    total,
                    number_of_people
                )

                if not verify_split(
                    total,
                    shares
                ):

                    st.error(
                        "❌ Split verification failed."
                    )

                    st.session_state[
                        "equal_split"
                    ] = None

                else:

                    st.session_state[
                        "equal_split"
                    ] = {
                        people[index]: shares[index]
                        for index in range(
                            number_of_people
                        )
                    }

                    set_scroll_target("equal-result-section")

            except Exception as error:

                st.error(
                    "Could not calculate equal split."
                )

                st.code(
                    str(error)
                )


        # ====================================================
        # DISPLAY EQUAL SPLIT
        # ====================================================

        if st.session_state[
            "equal_split"
        ] is not None:

            equal_split = st.session_state[
                "equal_split"
            ]

            st.markdown('<div id="equal-result-section"></div>', unsafe_allow_html=True)

            st.subheader(
                "💰 Each Person Pays"
            )

            for person, amount in equal_split.items():

                st.write(
                    f"**{person}:** "
                    f"₹{amount:.2f}"
                )


            st.divider()

            calculated_total = round_money(
                sum(
                    equal_split.values()
                )
            )

            receipt_total = round_money(
                confirmed_receipt.get(
                    "total",
                    0
                )
            )


            col1, col2 = st.columns(2)

            with col1:

                st.write(
                    f"**Calculated Total:** "
                    f"₹{calculated_total:.2f}"
                )

            with col2:

                st.write(
                    f"**Receipt Total:** "
                    f"₹{receipt_total:.2f}"
                )


            # =================================================
            # VERIFY EQUAL SPLIT
            # =================================================

            if verify_split(
                receipt_total,
                equal_split.values()
            ):

                st.success(
                    "✅ Equal split verified."
                )

                # =============================================
                # EMAIL SECTION
                # =============================================

                st.divider()

                st.subheader(
                    "📧 Share Split by Email"
                )

                email = st.text_input(
                    "Recipient Email",
                    placeholder="friend@gmail.com",
                    key="equal_split_email"
                )


                if st.button(
                    "📧 Send Split Results",
                    use_container_width=True,
                    key="send_equal_split_email"
                ):

                    if not email.strip():

                        st.error(
                            "Please enter an email address."
                        )

                    else:

                        try:

                            # For equal split, each person's
                            # subtotal is the same as their
                            # final share for this simplified
                            # email representation.
                            person_subtotals = {
                                person: round_money(
                                    amount
                                )
                                for person, amount
                                in equal_split.items()
                            }


                            send_split_email(
                            recipient_email=email.strip(),
                            merchant=confirmed_receipt.get(
                                "merchant",
                                "Unknown"
                            ),
                            person_subtotals=person_subtotals,
                            person_totals=equal_split,
                            tax=round_money(
                                confirmed_receipt.get(
                                    "tax",
                                    0
                                )
                            ),
                            discount=round_money(
                                confirmed_receipt.get(
                                    "discount",
                                    0
                                )
                            ),
                            receipt_total=receipt_total,
                            receipt_bytes=st.session_state.get(
                                "receipt_image"
                            ),
                            receipt_filename=st.session_state.get(
                                "receipt_filename"
                            )
                        )


                            st.success(
                                f"✅ Split results sent to {email.strip()}"
                            )

                        except Exception as error:

                            st.error(
                                "❌ Could not send the email."
                            )

                            st.code(
                                str(error)
                            )

            else:

                st.error(
                    "❌ Equal split verification failed."
                )


    # ========================================================
    # ITEM-BASED SPLIT
    # ========================================================

    else:

        st.subheader(
            "🛒 Item-Based Split"
        )

        st.caption(
            "Assign how many units of each item each person consumed."
        )

        items = confirmed_receipt.get(
            "items",
            []
        )


        # ====================================================
        # ASSIGNMENTS
        # ====================================================

        assignments = {
            person: {}
            for person in people
        }


        # ====================================================
        # ITEM ASSIGNMENT UI
        # ====================================================

        for item_index, item in enumerate(items):

            item_name = item.get(
                "name",
                f"Item {item_index + 1}"
            )

            item_quantity = int(
                item.get(
                    "quantity",
                    0
                )
            )

            item_total = float(
                item.get(
                    "total",
                    0
                )
            )


            info_col, people_col = st.columns(
                [1, 3]
            )

            with info_col:
                st.caption(item_name)
                st.write(
                    f"Qty: **{item_quantity}**  |  "
                    f"Total: **₹{item_total:.2f}**"
                )

            with people_col:
                cols = st.columns(number_of_people)


                for person_index, person in enumerate(people):

                    with cols[person_index]:

                        assigned_quantity = st.number_input(
                            f"{person}",
                            min_value=0,
                            max_value=item_quantity,
                            value=0,
                            step=1,
                            key=(
                                f"assign_"
                                f"{item_index}_"
                                f"{person_index}"
                            )
                        )

                        assignments[
                            person
                        ][
                            item_index
                        ] = assigned_quantity


            # =================================================
            # LIVE ASSIGNMENT VALIDATION
            # =================================================

            assigned_total = sum(
                assignments[person].get(
                    item_index,
                    0
                )
                for person in people
            )


            if assigned_total == item_quantity:

                st.success(
                    f"✅ {assigned_total}/"
                    f"{item_quantity} units assigned"
                )

            elif assigned_total < item_quantity:

                st.warning(
                    f"⚠️ {assigned_total}/"
                    f"{item_quantity} units assigned"
                )

            else:

                st.error(
                    f"❌ {assigned_total}/"
                    f"{item_quantity} units assigned"
                )


        # ====================================================
        # CALCULATE ITEM SPLIT
        # ====================================================

        if st.button(
            "🧮 Calculate Item Split",
            use_container_width=True
        ):

            try:

                person_subtotals = calculate_quantity_split(
                    items,
                    assignments
                )


                # =============================================
                # VERIFY ITEM ASSIGNMENT
                # =============================================

                if not verify_quantity_split(
                    items,
                    assignments,
                    person_subtotals
                ):

                    st.error(
                        "❌ Item quantities do not match the receipt."
                    )

                else:

                    # =========================================
                    # ALLOCATE TAX AND DISCOUNT
                    # =========================================

                    person_final_totals = (
                        allocate_tax_and_discount(
                            person_subtotals,
                            confirmed_receipt.get(
                                "tax",
                                0
                            ),
                            confirmed_receipt.get(
                                "discount",
                                0
                            ),
                            confirmed_receipt.get(
                                "total",
                                0
                            )
                        )
                    )


                    # =========================================
                    # SAVE RESULTS
                    # =========================================

                    st.session_state[
                        "quantity_split"
                    ] = person_final_totals

                    st.session_state[
                        "quantity_subtotals"
                    ] = person_subtotals

                    st.session_state[
                        "quantity_assignments"
                    ] = assignments


            except ValueError as error:

                st.error(
                    str(error)
                )

            except Exception as error:

                st.error(
                    "Could not calculate the item split."
                )

                st.code(
                    str(error)
                )


        # ====================================================
        # DISPLAY ITEM SPLIT
        # ====================================================

        if st.session_state[
            "quantity_split"
        ] is not None:

            person_final_totals = (
                st.session_state[
                    "quantity_split"
                ]
            )

            person_subtotals = (
                st.session_state[
                    "quantity_subtotals"
                ]
            )


            st.markdown('<div id="item-result-section"></div>', unsafe_allow_html=True)

            st.subheader(
                "💰 Final Item Split"
            )


            # =================================================
            # PERSON RESULTS
            # =================================================

            for person in person_final_totals:

                subtotal_amount = (
                    person_subtotals.get(
                        person,
                        0
                    )
                )

                final_amount = (
                    person_final_totals[
                        person
                    ]
                )


                st.write(
                    f"### {person}"
                )

                col1, col2 = st.columns(2)

                with col1:

                    st.write(
                        f"Items: "
                        f"₹{subtotal_amount:.2f}"
                    )

                with col2:

                    st.write(
                        f"Final: "
                        f"₹{final_amount:.2f}"
                    )


                st.divider()


            # =================================================
            # FINAL VERIFICATION
            # =================================================

            calculated_total = round_money(
                sum(
                    person_final_totals.values()
                )
            )

            original_total = round_money(
                confirmed_receipt.get(
                    "total",
                    0
                )
            )


            col1, col2 = st.columns(2)

            with col1:

                st.write(
                    f"**Calculated Total:** "
                    f"₹{calculated_total:.2f}"
                )

            with col2:

                st.write(
                    f"**Receipt Total:** "
                    f"₹{original_total:.2f}"
                )


            if verify_final_split(
                person_final_totals,
                original_total
            ):

                st.success(
                    "✅ Final split verified. "
                    "All amounts match the receipt total."
                )


                # =============================================
                # EMAIL SECTION
                # =============================================

                st.divider()

                st.subheader(
                    "📧 Share Split by Email"
                )

                email = st.text_input(
                    "Recipient Email",
                    placeholder="friend@gmail.com",
                    key="item_split_email"
                )


                if st.button(
                    "📧 Send Split Results",
                    use_container_width=True,
                    key="send_item_split_email"
                ):

                    if not email.strip():

                        st.error(
                            "Please enter an email address."
                        )

                    else:

                        try:

                            send_split_email(
                                recipient_email=email.strip(),
                                merchant=confirmed_receipt.get(
                                    "merchant",
                                    "Unknown"
                                ),
                                person_subtotals=person_subtotals,
                                person_totals=person_final_totals,
                                tax=round_money(
                                    confirmed_receipt.get(
                                        "tax",
                                        0
                                    )
                                ),
                                discount=round_money(
                                    confirmed_receipt.get(
                                        "discount",
                                        0
                                    )
                                ),
                                receipt_total=original_total
                            )


                            st.success(
                                f"✅ Split results sent to "
                                f"{email.strip()}"
                            )

                        except Exception as error:

                            st.error(
                                "❌ Could not send the email."
                            )

                            st.code(
                                str(error)
                            )


            else:

                st.error(
                    "❌ Final split verification failed."
                )


            # =================================================
            # TAX / DISCOUNT INFO
            # =================================================

            tax_amount = round_money(
                confirmed_receipt.get(
                    "tax",
                    0
                )
            )

            discount_amount = round_money(
                confirmed_receipt.get(
                    "discount",
                    0
                )
            )


            st.info(
                f"Tax allocated: "
                f"₹{tax_amount:.2f}  |  "
                f"Discount allocated: "
                f"₹{discount_amount:.2f}"
            )


# ============================================================
# CONFIRMED RECEIPT JSON
# ============================================================

if (
    st.session_state["receipt_confirmed"]
    and st.session_state["receipt"] is not None
):

    st.divider()

    with st.expander(
        "🔎 View Confirmed Receipt JSON"
    ):

        st.json(
            st.session_state["receipt"]
        )

# Smoothly move to the section affected by the latest successful action.
smooth_scroll_to_target()
