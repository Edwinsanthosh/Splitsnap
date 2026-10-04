from decimal import Decimal, ROUND_HALF_UP


# ============================================================
# Money Helpers
# ============================================================

def round_money(value):
    """
    Convert a value to Decimal and round it
    to exactly two decimal places.
    """

    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


# ============================================================
# Equal Split
# ============================================================

def calculate_equal_split(total, number_of_people):
    """
    Split the final bill equally among people.
    """

    if number_of_people <= 0:
        raise ValueError(
            "Number of people must be greater than zero."
        )

    total = round_money(total)

    base_share = (
        total / Decimal(number_of_people)
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    shares = [
        base_share
        for _ in range(number_of_people)
    ]

    current_total = sum(
        shares,
        Decimal("0.00")
    )

    difference = total - current_total

    if difference != Decimal("0.00"):
        shares[0] += difference

    return shares


# ============================================================
# Equal Split Verification
# ============================================================

def verify_split(total, shares):
    """
    Verify that all shares add up to the original bill.
    """

    total = round_money(total)

    calculated_total = sum(
        shares,
        Decimal("0.00")
    )

    calculated_total = round_money(
        calculated_total
    )

    return calculated_total == total


# ============================================================
# Quantity-Based Item Split
# ============================================================

def calculate_quantity_split(items, assignments):
    """
    Calculate each person's item subtotal based on
    the number of units they consumed.
    """

    person_totals = {
        person: Decimal("0.00")
        for person in assignments
    }

    item_assignments = {}

    # --------------------------------------------------------
    # Collect assigned quantities
    # --------------------------------------------------------

    for person, person_items in assignments.items():

        for item_index, quantity in person_items.items():

            quantity = int(quantity)

            if quantity < 0:
                raise ValueError(
                    "Assigned quantity cannot be negative."
                )

            if item_index not in item_assignments:
                item_assignments[item_index] = 0

            item_assignments[item_index] += quantity


    # --------------------------------------------------------
    # Calculate Item Subtotals
    # --------------------------------------------------------

    for item_index, item in enumerate(items):

        receipt_quantity = int(
            item.get("quantity", 0)
        )

        item_total = round_money(
            item.get("total", 0)
        )


        if receipt_quantity <= 0:

            raise ValueError(
                f"Invalid quantity for item: "
                f"{item.get('name', 'Unknown')}"
            )


        assigned_quantity = item_assignments.get(
            item_index,
            0
        )


        if assigned_quantity > receipt_quantity:

            raise ValueError(
                f"Too many units assigned for "
                f"'{item.get('name', 'Unknown')}'. "
                f"Receipt quantity: {receipt_quantity}, "
                f"assigned: {assigned_quantity}."
            )


        # ----------------------------------------------------
        # Require all units to be assigned
        # ----------------------------------------------------

        if assigned_quantity != receipt_quantity:

            raise ValueError(
                f"Not all units of "
                f"'{item.get('name', 'Unknown')}' "
                f"have been assigned."
            )


        # ----------------------------------------------------
        # Calculate Unit Price
        # ----------------------------------------------------

        unit_price = (
            item_total /
            Decimal(receipt_quantity)
        )


        # ----------------------------------------------------
        # Add Cost to Each Person
        # ----------------------------------------------------

        for person, person_items in assignments.items():

            quantity = int(
                person_items.get(
                    item_index,
                    0
                )
            )

            if quantity > 0:

                person_cost = (
                    unit_price *
                    Decimal(quantity)
                )

                person_totals[person] += person_cost


    # --------------------------------------------------------
    # Round Person Subtotals
    # --------------------------------------------------------

    for person in person_totals:

        person_totals[person] = round_money(
            person_totals[person]
        )


    return person_totals


# ============================================================
# Quantity Split Verification
# ============================================================

def verify_quantity_split(
    items,
    assignments,
    person_totals
):
    """
    Verify:

    1. No negative quantities.
    2. Every receipt quantity is assigned.
    3. No item is over-assigned.
    4. Person subtotals equal receipt item subtotal.
    """

    for item_index, item in enumerate(items):

        receipt_quantity = int(
            item.get("quantity", 0)
        )

        assigned_quantity = 0

        for person_items in assignments.values():

            assigned_quantity += int(
                person_items.get(
                    item_index,
                    0
                )
            )


        if assigned_quantity != receipt_quantity:
            return False


    receipt_subtotal = Decimal("0.00")

    for item in items:

        receipt_subtotal += round_money(
            item.get("total", 0)
        )


    people_subtotal = sum(
        person_totals.values(),
        Decimal("0.00")
    )


    return (
        round_money(receipt_subtotal)
        == round_money(people_subtotal)
    )


# ============================================================
# Allocate Tax and Discount
# ============================================================

def allocate_tax_and_discount(
    person_subtotals,
    tax,
    discount,
    final_total
):
    """
    Allocate tax and discount proportionally based
    on each person's item subtotal.

    The final returned amounts always add up exactly
    to the receipt's final total.
    """

    tax = round_money(tax)
    discount = round_money(discount)
    final_total = round_money(final_total)

    subtotal = sum(
        person_subtotals.values(),
        Decimal("0.00")
    )

    subtotal = round_money(subtotal)


    if subtotal <= Decimal("0.00"):

        raise ValueError(
            "Cannot allocate tax and discount because "
            "the item subtotal is zero."
        )


    person_totals = {}

    people = list(
        person_subtotals.keys()
    )


    # --------------------------------------------------------
    # Calculate proportional amounts
    # --------------------------------------------------------

    for person in people:

        person_subtotal = round_money(
            person_subtotals[person]
        )

        ratio = (
            person_subtotal /
            subtotal
        )


        person_tax = (
            tax * ratio
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )


        person_discount = (
            discount * ratio
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )


        person_total = (
            person_subtotal
            + person_tax
            - person_discount
        )


        person_totals[person] = round_money(
            person_total
        )


    # --------------------------------------------------------
    # Fix rounding difference
    # --------------------------------------------------------

    calculated_total = sum(
        person_totals.values(),
        Decimal("0.00")
    )

    difference = (
        final_total -
        calculated_total
    )


    if difference != Decimal("0.00"):

        # Put rounding difference on the person
        # with the largest subtotal.

        largest_person = max(
            people,
            key=lambda person:
                person_subtotals[person]
        )

        person_totals[
            largest_person
        ] += difference


    # --------------------------------------------------------
    # Final rounding
    # --------------------------------------------------------

    for person in person_totals:

        person_totals[person] = round_money(
            person_totals[person]
        )


    return person_totals


# ============================================================
# Final Bill Verification
# ============================================================

def verify_final_split(
    person_totals,
    final_total
):
    """
    Verify that all people's final amounts add up
    exactly to the receipt's final total.
    """

    calculated_total = sum(
        person_totals.values(),
        Decimal("0.00")
    )

    calculated_total = round_money(
        calculated_total
    )

    final_total = round_money(
        final_total
    )

    return calculated_total == final_total