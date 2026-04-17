import PyPDF2

def extract_text_from_pdf(pdf_path, output_txt_path):
    """
    Extract text from PDF and save as .txt file
    """
    try:
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text_content = ""
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text_content += f"===== Page {page_num + 1} [text layer] =====\n"
                text_content += page.extract_text() + "\n\n"
            
            # Save to text file
            with open(output_txt_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write(text_content)
            
            print(f"{pdf_path}Text extracted and saved to {output_txt_path}")
            
    except Exception as e:
        print(f"Error: {e}")

# Usage
extract_text_from_pdf('DATA/SOURCE DATA/SHA DATA/CONTRACTED-FACILITES-REHABILITATION.pdf', 'DATA/SOURCE DATA/TXT/CONTRACTED-FACILITIES-REHABILITATION.pdf.txt')
extract_text_from_pdf('DATA/SOURCE DATA/SHA DATA/SHA-FACILITIES-PAYMENT-ANALYSIS.pdf', 'DATA/SOURCE DATA/TXT/SHA-FACILITIES-PAYMENT-ANALYSIS.pdf.txt')
extract_text_from_pdf('DATA/SOURCE DATA/SHA DATA/CONTRACTED-FACILITIES-FBOs.pdf', 'DATA/SOURCE DATA/TXT/CONTRACTED-FACILITIES-FBOs.pdf.txt')
extract_text_from_pdf('DATA/SOURCE DATA/SHA DATA/CONTRACTED-FACILITIES-COUNTY-GOVT.pdf', 'DATA/SOURCE DATA/TXT/CONTRACTED-FACILITIES-COUNTY-GOVT.pdf.txt')
extract_text_from_pdf('DATA/SOURCE DATA/SHA DATA/CONTRACTED-FACILITIES-PRIVATE.pdf', 'DATA/SOURCE DATA/TXT/CONTRACTED-FACILITIES-PRIVATE.pdf.txt')
extract_text_from_pdf('DATA/SOURCE DATA/SHA DATA/CONTRACTED-FACILITIES-CLINICAL-FACILITIES.pdf', 'DATA/SOURCE DATA/TXT/CONTRACTED-FACILITIES-CLINICAL-FACILITIES.pdf.txt')
extract_text_from_pdf('DATA/SOURCE DATA/SHA DATA/CONTRACTED-FACILITIES-GOVERNMENT-OF-KENYA.pdf', 'DATA/SOURCE DATA/TXT/CONTRACTED-FACILITIES-GOVERNMENT-OF-KENYA.pdf.txt')
extract_text_from_pdf('DATA/SOURCE DATA/SHA DATA/CONTRACTED-FACILITIES-INSTITUTIONAL.pdf', 'DATA/SOURCE DATA/TXT/CONTRACTED-FACILITIES-INSTITUTIONAL.pdf.txt')
extract_text_from_pdf('DATA/SOURCE DATA/SHA DATA/CONTRACTED-FACILITIES-NGOs.pdf', 'DATA/SOURCE DATA/TXT/CONTRACTED-FACILITIES-NGOs.pdf.txt')
extract_text_from_pdf('DATA/SOURCE DATA/SHA DATA/CONTRACTED-FACILITIES-COMMUNITY-HOSP.pdf', 'DATA/SOURCE DATA/TXT/CONTRACTED-FACILITIES-COMMUNITY-HOSP.pdf.txt')