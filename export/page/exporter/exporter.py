import frappe
import csv
import os
from frappe.utils import get_site_path, get_files_path, nowdate
from frappe.utils.file_manager import save_file
from frappe.utils.pdf import get_pdf

@frappe.whitelist()
def export_supplier_quotations(from_date=None, to_date=None, supplier=None, format="CSV"):
    """Export supplier quotations based on filters"""
    
    # buildena le filtre
    filters = []
    if from_date:
        filters.append(["transaction_date", ">=", from_date])
    if to_date:
        filters.append(["transaction_date", "<=", to_date])
    if supplier:
        filters.append(["supplier", "=", supplier])
    
    # maka
    sq_list = frappe.get_list("Supplier Quotation",
        fields=["name", "supplier", "transaction_date", "grand_total", "status"],
        filters=filters,
        order_by="transaction_date"
    )
    
    if format == "CSV":
        return export_as_csv(sq_list)
    else:
        return export_as_pdf(sq_list, filters)

def export_as_csv(data):
    """Export data as CSV file"""
    file_name = f"supplier_quotations_{nowdate()}.csv"
    file_path = os.path.join(get_files_path(), file_name)
    
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["ID", "Supplier", "Date", "Amount", "Status"])
        
        for row in data:
            writer.writerow([
                row.name,
                row.supplier,
                row.transaction_date,
                row.grand_total,
                row.status
            ])
#Sauvgardena ao amin le fichier    
    with open(file_path, 'rb') as f:
        file_doc = save_file(file_name, f.read(), "File", "Home")
    
    return {
        "file_url": file_doc.file_url
    }
def export_as_pdf(data, filters):
    """Export data as PDF with proper template handling"""
    from frappe.utils import get_assets_json
    
    # preparena ao amin ilay template
    template_data = {
        "quotations": data,
        "filters": filters,
        "nowdate": frappe.utils.nowdate(),
        "company": frappe.defaults.get_user_default("company"),
        "print_settings": frappe.get_doc("Print Settings")
    }

    template_path = frappe.get_app_path("erpnext", "templates", "supplier_quotations_pdf.html")
    
    if not os.path.exists(template_path):
        frappe.throw(f"Template file not found at: {template_path}")

    # lire cont ilay template
    with open(template_path, "r") as template_file:
        html_content = template_file.read()

    html = frappe.render_template(html_content, template_data)

    #generena ilay pdf
    pdf_content = get_pdf(html)

    file_name = f"supplier_quotations_{frappe.utils.nowdate()}.pdf"
    file_doc = save_file(file_name, pdf_content, "File", "Home")
    
    return {"file_url": file_doc.file_url}