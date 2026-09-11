"""
Sample Legal PDF Generator
--------------------------
Generates realistic sample legal documents for instant zero-config testing:
1. Mutual Non-Disclosure Agreement (NDA)
2. Commercial Office Lease Agreement
3. Enterprise SaaS Terms of Service
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

SAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))

def create_pdf(filename: str, title: str, sections: list):
    filepath = os.path.join(SAMPLE_DIR, filename)
    doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        spaceAfter=15
    )

    section_heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=8
    )

    story = [Paragraph(title, title_style), Spacer(1, 10)]

    for sec_title, p_list in sections:
        if sec_title:
            story.append(Paragraph(sec_title, section_heading_style))
        for p_text in p_list:
            if p_text == "--- PAGE BREAK ---":
                story.append(PageBreak())
            else:
                story.append(Paragraph(p_text, body_style))
        story.append(Spacer(1, 6))

    doc.build(story)
    print(f"Generated sample document: {filename}")
    return filepath


def generate_all_samples():
    os.makedirs(SAMPLE_DIR, exist_ok=True)

    # 1. Mutual NDA
    nda_sections = [
        ("PREAMBLE", [
            "This Mutual Non-Disclosure Agreement ('Agreement') is entered into on January 15, 2025 ('Effective Date'), by and between Apex AI Technologies Corp., a Delaware corporation ('Disclosing Party'), and Nexus Legal Analytics Inc., a California corporation ('Receiving Party'). Party A and Party B are collectively referred to as the 'Parties'."
        ]),
        ("SECTION 1. CONFIDENTIAL INFORMATION", [
            "For purposes of this Agreement, 'Confidential Information' shall include all non-public, proprietary, or sensitive technical, business, financial, legal, or customer information disclosed by one Party to the other Party, whether orally, visually, or in writing.",
            "Confidential Information explicitly includes software source code, AI model weights, training datasets, client lists, and pricing schedules."
        ]),
        ("SECTION 2. OBLIGATIONS OF RECEIVING PARTY", [
            "The Receiving Party agrees to hold and maintain all Confidential Information in strict confidence using at least the same degree of care it uses to protect its own confidential information of like nature, but in no event less than reasonable care.",
            "The Receiving Party shall not disclose Confidential Information to any third party except to its officers, directors, employees, and legal advisors who have a strict need-to-know and are bound by confidentiality obligations at least as restrictive as those contained herein."
        ]),
        ("--- PAGE BREAK ---", []),
        ("SECTION 3. EXCLUSIONS FROM CONFIDENTIALITY", [
            "Confidential Information does not include information that: (a) is or becomes publicly available through no breach of this Agreement by Receiving Party; (b) was already rightfully in Receiving Party's possession prior to disclosure; (c) is independently developed by Receiving Party without reference to or reliance upon Disclosing Party's Confidential Information; or (d) is required to be disclosed by applicable court order or law."
        ]),
        ("SECTION 4. TERM AND TERMINATION", [
            "This Agreement shall commence on the Effective Date and remain in effect for a term of three (3) years. The confidentiality obligations under Section 2 shall survive termination of this Agreement for a period of five (5) years following disclosure.",
            "Either Party may terminate this Agreement at any time upon thirty (30) days written notice to the other Party."
        ]),
        ("SECTION 5. GOVERNING LAW AND REMEDIES", [
            "This Agreement shall be governed by and construed in accordance with the laws of the State of New York, without giving effect to conflict of law principles. Disclosing Party shall be entitled to seek injunctive relief in any court of competent jurisdiction to prevent unauthorized disclosure."
        ])
    ]
    create_pdf("Mutual_NDA_Agreement.pdf", "MUTUAL NON-DISCLOSURE AGREEMENT", nda_sections)

    # 2. Commercial Lease Agreement
    lease_sections = [
        ("PREAMBLE", [
            "This Commercial Office Lease Agreement ('Lease') is made effective as of March 1, 2025, by and between Metropolis Property Management LLC ('Lessor') and Horizon Tech Solutions Inc. ('Lessee')."
        ]),
        ("SECTION 1. DEMISED PREMISES AND USE", [
            "Lessor hereby leases to Lessee Suite 800 located on the 8th Floor of 500 Market Street, San Francisco, CA 94105 ('Premises'). The Premises shall be used exclusively for general commercial office and software engineering operations, and for no other purpose without Lessor's prior written consent."
        ]),
        ("SECTION 2. RENT AND SECURITY DEPOSIT", [
            "Lessee covenants to pay Lessor a base monthly rent of Twelve Thousand Five Hundred Dollars ($12,500.00), payable in advance on the first day of each calendar month.",
            "Upon execution of this Lease, Lessee shall deposit with Lessor the sum of Ten Thousand Dollars ($10,000.00) as a Security Deposit. The Security Deposit shall be returned to Lessee within thirty (30) days after Lessee vacates the Premises, less any deductions for repairs or unpaid rent."
        ]),
        ("SECTION 3. MAINTENANCE AND REPAIRS", [
            "Lessor shall maintain and repair structural components, foundation, exterior walls, roof, and central HVAC systems. Lessee shall maintain non-structural interior surfaces, light fixtures, and internal plumbing fixtures in good working condition."
        ]),
        ("--- PAGE BREAK ---", []),
        ("SECTION 4. SUBLETTING AND ASSIGNMENT", [
            "Lessee shall not assign this Lease or sublet any portion of the Premises without obtaining Lessor's prior written approval, which approval shall not be unreasonably withheld or delayed."
        ]),
        ("SECTION 5. TERMINATION NOTICE AND DEFAULT", [
            "In the event of non-payment of rent, Lessee shall have ten (10) business days following written notice to cure the default. Either party may terminate this Lease for convenience at the end of the initial 24-month term by providing at least ninety (90) days advance written notice."
        ])
    ]
    create_pdf("Commercial_Lease_Agreement.pdf", "COMMERCIAL OFFICE LEASE AGREEMENT", lease_sections)

    # 3. Enterprise SaaS Terms of Service
    saas_sections = [
        ("PREAMBLE", [
            "These Enterprise SaaS Terms of Service ('Terms') govern access to and use of the CloudScale Analytics Platform provided by CloudScale Systems Inc. ('Provider') to Enterprise Subscribers ('Customer')."
        ]),
        ("SECTION 1. SERVICE LEVEL AGREEMENT (SLA)", [
            "Provider guarantees a monthly Service Uptime Percentage of at least 99.9% for the CloudScale Platform, excluding scheduled maintenance windows announced at least 48 hours in advance.",
            "If Uptime falls below 99.9% in a calendar month, Customer is eligible to receive a service credit equal to 10% of monthly subscription fees upon written request submitted within 30 days."
        ]),
        ("SECTION 2. LIMITATION OF LIABILITY", [
            "TO THE MAXIMUM EXTENT PERMITTED BY LAW, IN NO EVENT SHALL PROVIDER BE LIABLE FOR INDIRECT, INCIDENTAL, CONSEQUENTIAL, SPECIAL, OR PUNITIVE DAMAGES.",
            "PROVIDER'S AGGREGATE CUMULATIVE LIABILITY ARISING OUT OF OR RELATED TO THIS AGREEMENT SHALL BE STRICTLY LIMITED TO THE TOTAL FEES PAID BY CUSTOMER TO PROVIDER IN THE TWELVE (12) MONTH PERIOD PRECEDING THE CLAIM."
        ]),
        ("--- PAGE BREAK ---", []),
        ("SECTION 3. INTELLECTUAL PROPERTY AND CUSTOMER DATA", [
            "Customer retains all ownership, rights, and title to all data, code, files, and legal documents uploaded to the Platform ('Customer Data'). Provider obtains no intellectual property rights in Customer Data except the limited license necessary to process requests.",
            "Provider retains exclusive rights and title to the Platform, AI algorithm architectures, system code, and all improvements thereto."
        ]),
        ("SECTION 4. MANDATORY ARBITRATION AND GOVERNING LAW", [
            "Any dispute, controversy, or claim arising under or relating to these Terms shall be settled by binding arbitration administered by the American Arbitration Association (AAA) under its Commercial Rules in Delaware. Judgment on the award rendered by the arbitrator may be entered in any court having jurisdiction."
        ])
    ]
    create_pdf("SaaS_Terms_of_Service.pdf", "ENTERPRISE SAAS TERMS OF SERVICE", saas_sections)

if __name__ == "__main__":
    generate_all_samples()
