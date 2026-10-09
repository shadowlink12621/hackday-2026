import os
from fpdf import FPDF

os.makedirs("sample_docs", exist_ok=True)

def create_medical_bill():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="APOLLO HOSPITALS ENTERPRISE LTD", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(200, 10, txt="Jubilee Hills, Hyderabad, Telangana 500033", ln=True, align='C')
    pdf.cell(200, 10, txt="GSTIN: 36AAACA1234A1Z5 | PAN: AAACA1234A", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="FINAL DISCHARGE BILL", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Arial", '', 11)
    pdf.cell(100, 8, txt="Patient Name: Mr. Rahul Sharma", ln=False)
    pdf.cell(100, 8, txt="Bill No: AHEL/2026/08912", ln=True)
    
    pdf.cell(100, 8, txt="UHID: 109847265", ln=False)
    pdf.cell(100, 8, txt="Date of Admission: 01-Oct-2026", ln=True)
    
    pdf.cell(100, 8, txt="Attending Dr: Dr. V. Reddy (Cardiology)", ln=False)
    pdf.cell(100, 8, txt="Date of Discharge: 05-Oct-2026", ln=True)
    pdf.ln(10)
    
    # Table Header
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(20, 10, "S.No", border=1)
    pdf.cell(100, 10, "Description of Service", border=1)
    pdf.cell(30, 10, "Category", border=1)
    pdf.cell(40, 10, "Amount (INR)", border=1, align='R')
    pdf.ln()
    
    # Table Content
    items = [
        ("1", "ICU Room Charge (4 Days @ 5000/day)", "Room Rent", "20000.00"),
        ("2", "Cardiologist Consultation Fees", "Consultation", "8000.00"),
        ("3", "ECG and Echo Test", "Diagnostics", "4500.00"),
        ("4", "Pharmacy - Prescribed Medicines", "Pharmacy", "3200.00"),
        ("5", "Surgical Gloves & Syringes", "Consumables", "1500.00"),
        ("6", "Dietary Services / Meals", "Non-Medical", "2000.00"),
    ]
    
    pdf.set_font("Arial", '', 11)
    for idx, desc, cat, amt in items:
        pdf.cell(20, 10, idx, border=1)
        pdf.cell(100, 10, desc, border=1)
        pdf.cell(30, 10, cat, border=1)
        pdf.cell(40, 10, amt, border=1, align='R')
        pdf.ln()
        
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(150, 10, "Total Amount Due:", border=1, align='R')
    pdf.cell(40, 10, "39200.00", border=1, align='R')
    
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 9)
    pdf.cell(200, 10, txt="This is a computer-generated invoice and does not require a signature.", ln=True, align='C')
    
    pdf.output("sample_docs/Apollo_Hospital_Bill_Sample.pdf")

def create_consumer_court_order():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="IN THE DISTRICT CONSUMER DISPUTES REDRESSAL COMMISSION", ln=True, align='C')
    pdf.cell(200, 10, txt="BENGALURU URBAN, KARNATAKA", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 8, txt="Consumer Complaint No: CC/1042/2026", ln=True, align='R')
    pdf.cell(200, 8, txt="Date of Order: 08-Oct-2026", ln=True, align='R')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 8, txt="BETWEEN:", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 8, txt="Mr. Amit Desai", ln=True)
    pdf.cell(200, 8, txt="Residing at: Koramangala, Bengaluru - 560034", ln=True)
    pdf.cell(200, 8, txt="... COMPLAINANT", ln=True, align='R')
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 8, txt="AND:", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 8, txt="Star Health & Allied Insurance Co. Ltd.", ln=True)
    pdf.cell(200, 8, txt="Branch Office: M.G. Road, Bengaluru", ln=True)
    pdf.cell(200, 8, txt="... OPPOSITE PARTY", ln=True, align='R')
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="ORDER / JUDGMENT", ln=True, align='C')
    
    pdf.set_font("Arial", '', 11)
    text = (
        "1. The Complainant has filed this complaint under Section 35 of the Consumer Protection Act, "
        "alleging deficiency of service by the Opposite Party for wrongfully repudiating a cashless health "
        "insurance claim (Claim ID: SH2026-99120) amounting to INR 45,000 for hospitalization related to Dengue Fever.\n\n"
        "2. The Opposite Party rejected the claim citing 'Non-disclosure of pre-existing disease (Hypertension)'. "
        "However, the Complainant provided medical records proving that the current hospitalization for Dengue "
        "is entirely unrelated to Hypertension.\n\n"
        "3. Upon reviewing the arguments and medical records, this Commission finds that the repudiation of the claim "
        "is arbitrary and constitutes a deficiency in service. The IRDAI guidelines strictly prohibit rejecting "
        "unrelated acute illness claims based on pre-existing lifestyle diseases unless a direct medical correlation exists.\n\n"
        "ORDER:\n"
        "The Opposite Party is hereby directed to:\n"
        "a) Pay the claim amount of INR 45,000 to the Complainant along with 9% interest p.a. from the date of repudiation.\n"
        "b) Pay INR 10,000 towards mental agony and litigation costs.\n"
        "Compliance shall be made within 45 days of this order."
    )
    pdf.multi_cell(0, 8, txt=text)
    
    pdf.ln(20)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(100, 8, txt="President", ln=False)
    pdf.cell(100, 8, txt="Member", ln=True, align='R')
    pdf.cell(100, 8, txt="District Consumer Commission", ln=False)
    
    pdf.output("sample_docs/Consumer_Court_Order_Insurance.pdf")

def create_corporate_expense():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(200, 10, txt="THE TAJ MAHAL PALACE, MUMBAI", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(200, 8, txt="Apollo Bunder, Mumbai, Maharashtra 400001", ln=True, align='C')
    pdf.cell(200, 8, txt="GSTIN: 27AAACT1234Z1Z9", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="TAX INVOICE - CORPORATE BILLING", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Arial", '', 11)
    pdf.cell(100, 8, txt="Guest Name: Ms. Priya Kapoor", ln=False)
    pdf.cell(100, 8, txt="Invoice No: TAJ-M-48291", ln=True)
    
    pdf.cell(100, 8, txt="Company: TechCorp India Pvt Ltd", ln=False)
    pdf.cell(100, 8, txt="Date: 02-Oct-2026", ln=True)
    pdf.ln(10)
    
    # Table
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(120, 10, "Description", border=1)
    pdf.cell(30, 10, "Qty", border=1, align='C')
    pdf.cell(40, 10, "Amount (INR)", border=1, align='R')
    pdf.ln()
    
    items = [
        ("Business Dinner (Sea Lounge)", "1", "3450.00"),
        ("Client Meeting - Coffee/Snacks", "2", "1200.00"),
        ("Airport Transfer (Sedan)", "1", "1800.00"),
    ]
    
    pdf.set_font("Arial", '', 11)
    for desc, qty, amt in items:
        pdf.cell(120, 10, desc, border=1)
        pdf.cell(30, 10, qty, border=1, align='C')
        pdf.cell(40, 10, amt, border=1, align='R')
        pdf.ln()
        
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(150, 10, "Sub Total:", border=1, align='R')
    pdf.cell(40, 10, "6450.00", border=1, align='R')
    pdf.ln()
    pdf.cell(150, 10, "GST (18%):", border=1, align='R')
    pdf.cell(40, 10, "1161.00", border=1, align='R')
    pdf.ln()
    pdf.cell(150, 10, "Grand Total:", border=1, align='R')
    pdf.cell(40, 10, "7611.00", border=1, align='R')
    
    pdf.output("sample_docs/Corporate_Expense_Taj_Hotel.pdf")

if __name__ == "__main__":
    create_medical_bill()
    create_consumer_court_order()
    create_corporate_expense()
    print("Successfully generated Indian sample documents in sample_docs/ folder.")
