import frappe
import csv
import io
from datetime import datetime

DEFAULT_WAREHOUSE = "Stores"  


def verifier_entrepot(nom_entrepot):
    COMPANY_ABBR = "EM"  
    DEFAULT_WAREHOUSE = "Stores"  
    nom_complet = f"{nom_entrepot.strip()} - {COMPANY_ABBR}"
    
    if not frappe.db.exists("Warehouse", nom_complet):
        frappe.get_doc({
            "doctype": "Warehouse",
            "warehouse_name": nom_entrepot.strip(),
            "parent_warehouse": "All Warehouses - EM",
            "company": frappe.defaults.get_user_default("Company")
        }).insert(ignore_permissions=True)
    
    return nom_complet

    
def creeItemGroup(item_group_name):
    """Crée un groupe d'article s'il n'existe pas"""
    if not frappe.db.exists("Item Group", item_group_name):
        item_group = frappe.new_doc("Item Group")
        item_group.update({
            "item_group_name": item_group_name,
            "parent_item_group": "All Item Groups"  
        })
        item_group.insert(ignore_permissions=True)
        return True
    return False
    
def creeItem(item_name, item_group):
    """Crée un article avec toutes les métadonnées nécessaires"""
    if not frappe.db.exists("Item", item_name):
        item = frappe.new_doc("Item")
        item.update({
            "item_code": item_name,
            "item_name": item_name,
            "item_group": item_group,
            "stock_uom": "Unit",
            "is_stock_item": 1,
            "include_item_in_manufacturing": 0
        })
        
        # Configuration obligatoire des UOM
        item.append("uoms", {
            "uom": "Unit",
            "conversion_factor": 1.0,
            "must_be_whole_number": 0
        })
        
        try:
            item.insert(ignore_permissions=True)
            frappe.db.commit()
            return True
        except Exception as e:
            frappe.log_error(f"Erreur création item {item_name}: {str(e)}")
            return False
    return False
def get_item_uom_details(item_code):
    """Récupère les infos UOM d'un item avec des valeurs par défaut"""
    if not frappe.db.exists("Item", item_code):
        return {"uom": "Unit", "conversion_factor": 1.0}
    
    doc = frappe.get_doc("Item", item_code)
    return {
        "uom": doc.stock_uom or "Unit",
        "conversion_factor": 1.0,
        "stock_uom": doc.stock_uom or "Unit"
    }


def creer_material_request(items, ref):
    """Crée une Material Request complète"""
    mr = frappe.new_doc("Material Request")
    mr.update({
        "material_request_type": "Purchase",
        "transaction_date": datetime.strptime(items[0]['date'], '%d/%m/%Y').date(),
        "schedule_date": datetime.strptime(items[0]['required_by'], '%d/%m/%Y').date(),
        "company": frappe.defaults.get_user_default("Company"),
        "status": "Stopped",  # Statut initial
        "items": []
    })
    
    for item in items:
        item_doc = frappe.get_doc("Item", item['item_name'])
        
        mr.append("items", {
            "item_code": item['item_name'],
            "item_name": item['item_name'],
            "description": item_doc.description or item['item_name'],
            "qty": float(item['quantity']),
            "uom": item_doc.stock_uom,
            "stock_uom": item_doc.stock_uom,
            "conversion_factor": 1.0,
            "stock_qty": float(item['quantity']),
            "schedule_date": datetime.strptime(item['required_by'], '%d/%m/%Y').date(),
            "warehouse": verifier_entrepot(item.get('target_warehouse', DEFAULT_WAREHOUSE))
        })
    
    mr.insert(ignore_permissions=True)
    mr.submit()
    return mr.name

def creer_request_for_quotation(mr_name, suppliers, ref, items_data):
    """Crée un Request for Quotation complet"""
    mr = frappe.get_doc("Material Request", mr_name)
    
    rfq = frappe.new_doc("Request for Quotation")
    rfq.update({
        "transaction_date": datetime.strptime(items_data[0]['date'], '%d/%m/%Y').date(),
        "company": frappe.defaults.get_user_default("Company"),
        "schedule_date": datetime.strptime(items_data[0]['required_by'], '%d/%m/%Y').date(),
        "status": "Submitted",
        "message_for_supplier": "Veuillez fournir votre meilleure offre",
        "suppliers": [],
        "items": []
    })
    
    for supplier in suppliers:
        supplier_doc = frappe.get_doc("Supplier", supplier)
        rfq.append("suppliers", {
            "supplier": supplier,
            "supplier_name": supplier_doc.supplier_name,
            "contact": supplier_doc.supplier_primary_contact or "",
            "email_id": supplier_doc.email_id or ""
        })
    
    for item in mr.items:
        item_doc = frappe.get_doc("Item", item.item_code)
        rfq.append("items", {
            "item_code": item.item_code,
            "item_name": item.item_name,
            "description": item_doc.description or item.item_name,
            "qty": item.qty,
            "stock_qty": item.qty,
            "uom": item.uom,
            "stock_uom": item_doc.stock_uom,
            "conversion_factor": 1.0,
            "schedule_date": item.schedule_date,
            "warehouse": item.warehouse
        })
    
    rfq.insert(ignore_permissions=True)
    rfq.submit()
    return rfq.name

def creer_supplier_quotation(rfq_name, mr_name, supplier, items):
    """Crée un Supplier Quotation complet"""
    sq = frappe.new_doc("Supplier Quotation")
    sq.update({
        "supplier": supplier,
        "company": frappe.defaults.get_user_default("Company"),
        "currency": frappe.db.get_value("Company", frappe.defaults.get_user_default("Company"), "default_currency"),
        "conversion_rate": 1.0,
        "buying_price_list": "Standard Buying",
        "price_list_currency": frappe.db.get_value("Price List", "Standard Buying", "currency"),
        "plc_conversion_rate": 1.0,
        "transaction_date": frappe.utils.nowdate(),
        "valid_till": frappe.utils.add_days(frappe.utils.nowdate(), 30),
        "request_for_quotation": rfq_name,
        "material_request": mr_name,
        "status": "Draft"
    })
    
    for item in items:
        item_doc = frappe.get_doc("Item", item['item_name'])
        
        sq.append("items", {
            "item_code": item['item_name'],
            "item_name": item['item_name'],
            "description": item_doc.description or item['item_name'],
            "qty": float(item['quantity']),
            "uom": item_doc.stock_uom,
            "stock_uom": item_doc.stock_uom,
            "conversion_factor": 1.0,
            "stock_qty": float(item['quantity']),
            "rate": 0,
            "schedule_date": datetime.strptime(item['required_by'], '%d/%m/%Y').date(),
            "warehouse": verifier_entrepot(item.get('target_warehouse', DEFAULT_WAREHOUSE))
        })
    
    sq.insert(ignore_permissions=True)
   
    return sq.name

@frappe.whitelist()
def import_supplier_quotations(items_data, suppliers_data):
    """Fonction principale pour l'import des devis fournisseurs"""
    result_messages = []
    
    # Traitement des fichiers CSV
    items_csv = io.StringIO(items_data)
    items_reader = csv.DictReader(items_csv, delimiter=',')
    items_by_ref = {}
    
    for row in items_reader:
        ref = row.get('ref')
        if ref:
            if ref not in items_by_ref:
                items_by_ref[ref] = []
            items_by_ref[ref].append(row)
    
    suppliers_csv = io.StringIO(suppliers_data)
    suppliers_reader = csv.DictReader(suppliers_csv, delimiter=',')
    suppliers_by_ref = {}
    
    for row in suppliers_reader:
        ref = row.get('ref_request_quotation')
        if ref:
            if ref not in suppliers_by_ref:
                suppliers_by_ref[ref] = []
            suppliers_by_ref[ref].append(row.get('supplier'))
    
    # Phase 1: Vérification et création des items
    for ref in items_by_ref:
        for item_row in items_by_ref[ref]:
            item_name = item_row['item_name']
            item_group = item_row.get('item_groupe', 'Consommable')
            
            if not frappe.db.exists("Item", item_name):
                try:
                    if creeItem(item_name, item_group):
                        result_messages.append(f"✅ Article créé: {item_name}")
                    else:
                        result_messages.append(f"❌ Échec création article {item_name}")
                except Exception as e:
                    result_messages.append(f"❌ Erreur création article {item_name}: {str(e)}")
                    frappe.log_error(f"Erreur création article {item_name}", str(e))
    
    # Phase 2: Traitement par référence
    for ref in items_by_ref:
        if ref not in suppliers_by_ref:
            result_messages.append(f"⚠️ Aucun fournisseur pour référence {ref}")
            continue
        
        items = items_by_ref[ref]
        suppliers = suppliers_by_ref[ref]
        
        try:
            # 1. Créer Material Request
            mr_name = creer_material_request(items, ref)
            result_messages.append(f"✅ MR créée: {mr_name} (réf: {ref})")
            
            # 2. Créer Request for Quotation
            rfq_name = creer_request_for_quotation(mr_name, suppliers, ref, items)
            result_messages.append(f"✅ RFQ créé: {rfq_name} (réf: {ref})")
            
            # 3. Créer Supplier Quotations
            for supplier in suppliers:
                if not frappe.db.exists("Supplier", supplier):
                    result_messages.append(f"⚠️  Fournisseur inexistant: {supplier}")
                    continue
                
                try:
                    sq_name = creer_supplier_quotation(rfq_name, mr_name, supplier, items)
                    result_messages.append(f"✅ Devis créé pour {supplier}: {sq_name}")
                except Exception as e:
                    error_msg = f"❌ Erreur devis {supplier}: {str(e)}"
                    result_messages.append(error_msg)
                    frappe.log_error("Erreur création SQ", error_msg)
        
        except Exception as e:
            error_msg = f"⚠️ Erreur référence {ref}: {str(e)}"
            result_messages.append(error_msg)
            frappe.log_error("Erreur traitement référence", error_msg)
    
    return result_messages