import urllib.request
import re
import os

os.makedirs('sample_docs/real_data', exist_ok=True)

# Real Supreme Court Judgment: Biman Krishna Bose vs United India Insurance Co.
url1 = 'https://indiankanoon.org/doc/1712542/'
req1 = urllib.request.Request(url1, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req1) as response:
        html = response.read().decode('utf-8')
        match = re.search(r'<div class="judgments">(.*?)</div>', html, re.DOTALL | re.IGNORECASE)
        text = match.group(1) if match else html
        clean_text = re.sub(r'<[^>]+>', ' ', text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        with open('sample_docs/real_data/Supreme_Court_Biman_Bose_vs_United_India_Insurance.txt', 'w', encoding='utf-8') as f:
            f.write(f"SOURCE: Indian Kanoon\nURL: {url1}\n\n{clean_text[:5000]}...\n[TRUNCATED FOR SAMPLE]")
        print("Downloaded Real Judgment: Biman Bose vs United India Insurance")
except Exception as e:
    print("Failed to download Judgment:", e)

# Real IRDAI Health Insurance Regulations (2016)
url2 = 'https://irdai.gov.in/documents/37343/931203/Health+Insurance+Regulations%2C+2016.pdf'
req2 = urllib.request.Request(url2, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req2) as response:
        pdf_data = response.read()
        with open('sample_docs/real_data/IRDAI_Health_Insurance_Regulations_2016.pdf', 'wb') as f:
            f.write(pdf_data)
        print("Downloaded Real Document: IRDAI Health Insurance Regulations 2016 PDF")
except Exception as e:
    print("Failed to download IRDAI PDF:", e)

# Real National Consumer Disputes Redressal Commission (NCDRC) order sample from public API/domain
url3 = 'https://indiankanoon.org/doc/848242/' # United India Insurance vs Harchand Rai Chandan Lal
req3 = urllib.request.Request(url3, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req3) as response:
        html = response.read().decode('utf-8')
        match = re.search(r'<div class="judgments">(.*?)</div>', html, re.DOTALL | re.IGNORECASE)
        text = match.group(1) if match else html
        clean_text = re.sub(r'<[^>]+>', ' ', text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        with open('sample_docs/real_data/Supreme_Court_United_India_vs_Harchand_Rai.txt', 'w', encoding='utf-8') as f:
            f.write(f"SOURCE: Indian Kanoon\nURL: {url3}\n\n{clean_text[:5000]}...\n[TRUNCATED FOR SAMPLE]")
        print("Downloaded Real Judgment: United India Insurance vs Harchand Rai")
except Exception as e:
    print("Failed to download Judgment:", e)
