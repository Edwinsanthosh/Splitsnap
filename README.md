# 🧾 SplitSnap — AI Receipt & Bill Splitter

SplitSnap is an AI-powered receipt and bill splitting application built with **Streamlit**, **Google Gemini Vision**, and **Python**.

The application allows a user to:

1. Upload a receipt image.
2. Analyze the receipt using Gemini Vision.
3. Extract structured receipt information.
4. Review and edit the extracted data.
5. Split the bill equally or by individual items.
6. Automatically allocate tax and discount.
7. Verify that the calculated split matches the original receipt total.
8. Share the final split through email.

The project follows the same simple Streamlit + Gemini workflow used in the provided MacroSnap guide: local Python environment → Gemini API configuration → Streamlit application → secrets configuration → deployment.

---

## 🚀 Features

### 📷 Receipt Upload
Upload a receipt in:

- JPG
- JPEG
- PNG
- WEBP

The receipt image is sent to Gemini Vision for analysis.

### 🤖 AI Receipt Extraction

Gemini extracts:

- Merchant name
- Item name
- Quantity
- Unit price
- Item total
- Subtotal
- Tax
- Discount
- Final total

The response is converted into structured JSON before being used by the application.

### 📝 Receipt Review

Before splitting the bill, the user can edit:

- Merchant
- Item names
- Quantities
- Unit prices
- Item totals
- Subtotal
- Tax
- Discount
- Final total

### ⚖️ Equal Split

The total receipt amount can be divided equally between multiple people.

The application uses decimal-based money calculations and verifies that the calculated shares add up exactly to the receipt total.

### 🛒 Item-Based Split

Users can assign quantities of individual items to different people.

For example:

```text
Cheese Burger × 4

Edwin    → 1
John     → 1
Rahul    → 2
```

SplitSnap calculates each person's item subtotal based on the quantity they consumed.

### 💰 Tax & Discount Allocation

Tax and discount are allocated proportionally based on each person's item subtotal.

The final amounts are adjusted for rounding differences so that:

```text
Sum of everyone's amount = Receipt final total
```

### ✅ Split Verification

The application verifies:

- All receipt item quantities are assigned.
- No item quantity is over-assigned.
- Item subtotals match the receipt.
- Final split amounts match the receipt total.

### 📧 Email Sharing

After a successful split, the result can be sent to a recipient using Gmail SMTP with a Gmail App Password.

---

# 🏗️ Project Structure

```text
SplitSnap/
│
├── app.py
├── prompts.py
├── receipt_parser.py
├── splitter.py
├── whatsapp.py
├── email_sender.py
├── requirements.txt
├── .gitignore
│
└── .streamlit/
    └── secrets.toml
```

> Some files from the original planned structure may not be required by the current implementation. Keep the README aligned with the files actually present in your repository.

---

# 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Streamlit | Web interface |
| Google Gemini | Receipt image analysis |
| Google GenAI SDK | Gemini API integration |
| Decimal | Accurate money calculations |
| Gmail SMTP | Email sharing |
| Git/GitHub | Source-code management |
| Streamlit Community Cloud | Deployment |

---

# 📋 Prerequisites

Before starting, install:

- Python 3.9+
- Git
- A Google account
- A Gemini API key
- A Gmail account with 2-Step Verification enabled if email sharing is required

---

# 1️⃣ Clone the Repository

Clone the project:

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
```

Move into the project:

```bash
cd Splitsnap
```

---

# 2️⃣ Create a Virtual Environment

Create the virtual environment:

### Windows

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

---

# 3️⃣ Install Dependencies

Create or verify `requirements.txt`.

Example:

```txt
streamlit
google-genai
```

If email sharing is enabled, no additional SMTP package is required because Python's built-in `smtplib` is used.

If your repository contains additional imports, include those packages in `requirements.txt`.

Install everything:

```bash
pip install -r requirements.txt
```

---

# 4️⃣ Create a Gemini API Key

SplitSnap uses Google Gemini to analyze receipt images.

Create a Gemini API key from Google AI Studio.

After obtaining the key, do **not** place it directly inside `app.py`.

Instead, use Streamlit secrets.

---

# 5️⃣ Configure Streamlit Secrets

Create this folder:

```text
.streamlit/
```

Inside it create:

```text
secrets.toml
```

Example:

```toml
GEMINI_API_KEY = "your-gemini-api-key"

GMAIL_ADDRESS = "your-gmail@gmail.com"
GMAIL_APP_PASSWORD = "your-gmail-app-password"
```

Replace the placeholder values with your actual credentials.

### Important

Never commit:

```text
.streamlit/secrets.toml
```

to GitHub.

Add it to `.gitignore`:

```gitignore
.streamlit/secrets.toml
venv/
__pycache__/
.env
```

---

# 6️⃣ Configure Gmail App Password

Email sharing uses Gmail SMTP.

For Gmail:

1. Enable **2-Step Verification** on your Google account.
2. Open your Google Account security settings.
3. Create an **App Password**.
4. Use the generated App Password as:

```toml
GMAIL_APP_PASSWORD = "your-app-password"
```

Do not use your normal Gmail password.

---

# 7️⃣ Run SplitSnap Locally

Start Streamlit:

```bash
streamlit run app.py
```

Streamlit will provide a local address similar to:

```text
http://localhost:8501
```

Open it in your browser.

---

# 🔄 Application Flow

The complete application flow is:

```text
Upload Receipt
      ↓
Gemini Vision Analysis
      ↓
Structured Receipt JSON
      ↓
Review & Edit Receipt
      ↓
Confirm Receipt
      ↓
Choose Number of People
      ↓
Choose Split Method
      ↓
 ┌──────────────────────┐
 │                      │
 ▼                      ▼
Equal Split       Item-Based Split
 │                      │
 │                 Assign Quantities
 │                      │
 │                 Calculate Subtotals
 │                      │
 └──────────┬───────────┘
            ↓
     Tax / Discount Allocation
            ↓
       Final Verification
            ↓
       Email the Results
```

---

# 🤖 Gemini Receipt Processing

The application sends the uploaded receipt image to Gemini together with a structured extraction prompt.

Gemini is instructed to return JSON in this format:

```json
{
  "merchant": "string",
  "items": [
    {
      "name": "string",
      "quantity": 1,
      "unit_price": 0,
      "total": 0
    }
  ],
  "subtotal": 0,
  "tax": 0,
  "discount": null,
  "total": 0
}
```

The application cleans the response before parsing it with Python's JSON parser.

This prevents Markdown code fences such as:

```text
```json
...
```
```

from causing JSON parsing errors.

---

# 💵 Bill Splitting Logic

## Equal Split

If:

```text
Receipt total = ₹100
People = 3
```

the application calculates:

```text
Person 1 → ₹33.34
Person 2 → ₹33.33
Person 3 → ₹33.33
```

The one-cent/paise rounding difference is assigned to one person so that:

```text
₹33.34 + ₹33.33 + ₹33.33 = ₹100.00
```

---

## Item-Based Split

Suppose:

```text
Burger × 4 = ₹400
```

and:

```text
Edwin → 1
John  → 1
Rahul → 2
```

Then:

```text
Burger unit price = ₹100

Edwin → ₹100
John  → ₹100
Rahul → ₹200
```

The application performs this calculation for every receipt item.

---

# 🧮 Tax and Discount

After calculating each person's item subtotal, SplitSnap proportionally allocates:

- Tax
- Discount

The final amount is then calculated for every person.

A final verification ensures:

```text
Sum of individual totals
=
Receipt final total
```

---

# 📧 Email Sharing

Once the split has been successfully verified, the user can enter a recipient email.

Example:

```text
Recipient Email:
friend@gmail.com
```

SplitSnap sends the calculated bill split through Gmail SMTP.

---

# 🧪 Testing Locally

Before deployment, test the complete flow:

### Test 1 — Receipt Upload

Upload a clear receipt image.

Expected:

```text
Receipt analyzed successfully
```

### Test 2 — Receipt Review

Verify:

- Merchant
- Item names
- Quantities
- Prices
- Tax
- Discount
- Final total

### Test 3 — Equal Split

Try:

```text
2 people
3 people
4 people
```

Check that the total always matches the receipt.

### Test 4 — Item-Based Split

Test:

```text
1 person consumes all items
Multiple people consume different quantities
```

Also test incomplete assignments.

The application should prevent calculation when item quantities are not fully assigned.

### Test 5 — Email

Send a test result to your own email address.

---

# 📦 Prepare the Project for GitHub

Before pushing the project, verify that sensitive files are ignored.

Check:

```bash
git status
```

Make sure this file does **not** appear:

```text
.streamlit/secrets.toml
```

Then:

```bash
git add .
git commit -m "Initial SplitSnap implementation"
git push origin main
```

---

# ☁️ Deployment with Streamlit Community Cloud

The deployment process follows the same general approach as the provided MacroSnap guide.

## 1. Push the Project to GitHub

Your repository should contain the application code and dependency files.

Example:

```text
Splitsnap/
├── app.py
├── splitter.py
├── email_sender.py
├── requirements.txt
├── .gitignore
└── .streamlit/
    └── secrets.toml   ← DO NOT PUSH THIS
```

The actual `secrets.toml` remains local.

---

## 2. Open Streamlit Community Cloud

Go to Streamlit Community Cloud and sign in using your GitHub account.

Create a new application.

---

## 3. Select the Repository

Choose:

```text
Repository → Your SplitSnap repository
```

Select the branch containing the application.

For example:

```text
main
```

Set the main application file to:

```text
app.py
```

Deploy the application.

---

# 🔐 4. Add Secrets in Streamlit Cloud

After opening the deployed application's settings, add the same secrets that were used locally.

Example:

```toml
GEMINI_API_KEY = "your-gemini-api-key"

GMAIL_ADDRESS = "your-gmail@gmail.com"
GMAIL_APP_PASSWORD = "your-gmail-app-password"
```

Do **not** upload your local `secrets.toml` to GitHub.

The cloud deployment should receive these values through Streamlit's Secrets configuration.

---

# 🚀 5. Deploy

After configuring the repository and secrets, deploy the application.

Streamlit will:

```text
Clone GitHub repository
        ↓
Install requirements.txt
        ↓
Configure secrets
        ↓
Start Streamlit
        ↓
Generate public application URL
```

Once deployment finishes, open the generated URL and test the complete application.

---

# 🔍 Deployment Checklist

Before considering the deployment complete:

- [ ] Repository pushed to GitHub
- [ ] `app.py` exists
- [ ] `requirements.txt` exists
- [ ] `.gitignore` exists
- [ ] `secrets.toml` is NOT committed
- [ ] Gemini API key added to Streamlit Secrets
- [ ] Gmail address added to Streamlit Secrets
- [ ] Gmail App Password added to Streamlit Secrets
- [ ] Application starts successfully
- [ ] Receipt upload works
- [ ] Gemini extraction works
- [ ] Receipt review works
- [ ] Equal split works
- [ ] Item-based split works
- [ ] Tax/discount allocation works
- [ ] Final verification works
- [ ] Email sharing works

---

# 🐛 Common Problems

## Gemini API Key Error

Check:

```toml
GEMINI_API_KEY = "..."
```

Make sure the secret name exactly matches the name used in `app.py`.

---

## Invalid JSON from Gemini

The application already cleans Markdown code fences before parsing the Gemini response.

If extraction still fails, try:

- A clearer receipt image.
- Better lighting.
- A higher-resolution image.
- A supported receipt format.

---

## Email Authentication Error

Check:

- Gmail address
- 2-Step Verification
- App Password
- Streamlit secrets

Do not use the normal Gmail account password.

---

## Module Not Found

Install dependencies:

```bash
pip install -r requirements.txt
```

If a new Python package is imported into the application, add it to:

```text
requirements.txt
```

and redeploy.

---

# 🔒 Security

Never expose:

```text
GEMINI_API_KEY
GMAIL_APP_PASSWORD
```

inside source code.

Never commit:

```text
.streamlit/secrets.toml
```

to GitHub.

If a secret is accidentally committed, revoke it and generate a new credential.

---

# 📁 Recommended Final Repository

```text
Splitsnap/
│
├── app.py
├── splitter.py
├── email_sender.py
├── requirements.txt
├── .gitignore
├── README.md
│
└── .streamlit/
    └── secrets.toml.example
```

A safe `secrets.toml.example` can contain:

```toml
GEMINI_API_KEY = "your-gemini-api-key"
GMAIL_ADDRESS = "your-gmail@gmail.com"
GMAIL_APP_PASSWORD = "your-gmail-app-password"
```

This example file contains placeholders only and can safely be committed.

---

# 🎯 Project Goal

SplitSnap demonstrates how an AI vision model can be combined with traditional Python application logic.

Instead of asking Gemini to perform the complete bill-splitting calculation, the application uses Gemini primarily for **receipt understanding and structured extraction**, while Python handles:

- Validation
- Quantity assignment
- Money calculations
- Tax allocation
- Discount allocation
- Final verification

This keeps the financial calculations deterministic and easier to verify.

---

# 📌 Development Flow

```text
Project Setup
      ↓
Gemini API Setup
      ↓
Receipt Upload
      ↓
Gemini Vision
      ↓
Structured JSON
      ↓
Receipt Review
      ↓
Equal Split
      ↓
Item-Based Split
      ↓
Tax / Discount Allocation
      ↓
Validation
      ↓
Email Sharing
      ↓
Testing
      ↓
GitHub
      ↓
Streamlit Community Cloud
      ↓
Deployment
```

---

## License

Add your preferred license here if you plan to publish the project publicly.
