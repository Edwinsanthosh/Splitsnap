import streamlit as st

from email_sender import send_split_email


st.title("SplitSnap Email Test")

recipient = st.text_input(
    "Enter recipient email"
)


if st.button("Send Test Email"):

    if not recipient:

        st.error(
            "Please enter an email address."
        )

    else:

        try:

            send_split_email(
                recipient_email=recipient,
                merchant="IKEA Food Place",
                person_totals={
                    "Edwin": 12.45,
                    "Rahul": 9.83,
                    "Arun": 9.82
                },
                receipt_total=32.10
            )

            st.success(
                "✅ Email sent successfully!"
            )

        except Exception as error:

            st.error(
                "❌ Failed to send email."
            )

            st.code(
                str(error)
            )