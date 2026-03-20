import requests
from bs4 import BeautifulSoup
import json
import sqlite3
import pandas as pd
from datetime import datetime
import time

print("El script ha iniciado correctamente.")

# -----------------------------
# CONFIG
# -----------------------------
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

BASE_URL = "https://lebump.com.mx"


# -----------------------------
# GUARDAR EN BASE DE DATOS
# -----------------------------
def save_to_db(df):
    conn = sqlite3.connect("inventario.db")

    df.to_sql(
        "inventario",
        conn,
        if_exists="append",
        index=False
    )

    conn.close()


# -----------------------------
# OBTENER TODOS LOS PRODUCTOS
# -----------------------------
def get_all_products():
    all_products = []
    base_url = f"{BASE_URL}/products.json"
    page = 1
    limit = 250  # más seguro que 350

    while True:
        url = f"{base_url}?page={page}&limit={limit}"
        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            print(f"Error al obtener productos (page {page})")
            break

        data = response.json()

        if not data.get('products'):
            break

        all_products.extend(data['products'])
        print(f"Página {page} procesada ({len(data['products'])} productos)")

        page += 1
        time.sleep(0.5)  # evitar bloqueos

    return all_products


# -----------------------------
# EXTRAER INVENTARIO
# -----------------------------
def extract_inventory(product, product_data):
    try:
        handle = product['handle']
        product_url = f"{BASE_URL}/products/{handle}"

        response = requests.get(product_url, headers=HEADERS)

        if response.status_code != 200:
            print(f"Error en {product_url}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')

        script_tag = soup.find('script', {
            'type': 'application/json',
            'data-product-inventory-json': True
        })

        if not script_tag:
            print(f"No inventory JSON en {product_url}")
            return

        inventory_data = json.loads(script_tag.string)

        for key, value in inventory_data.get('inventory', {}).items():
            inventory_id = key
            inventory_quantity = value.get('inventory_quantity', 0)

            product_data.append({
                'product_url': product_url,
                'product_name': handle,
                'inventory_id': inventory_id,
                'inventory_quantity': inventory_quantity
            })

    except Exception as e:
        print(f"Error al procesar {product.get('handle')}: {e}")


# -----------------------------
# FUNCIÓN PRINCIPAL
# -----------------------------
def scrape_and_save():
    product_data = []

    print("Obteniendo productos...")
    products = get_all_products()

    print(f"Total productos encontrados: {len(products)}")

    for i, product in enumerate(products):
        print(f"Procesando {i+1}/{len(products)}: {product['handle']}")

        extract_inventory(product, product_data)

        time.sleep(0.5)  # evitar bloqueos

    # Convertir a DataFrame
    df_new = pd.DataFrame(product_data)

    # Agregar timestamp
    df_new['timestamp'] = datetime.now()

    # Guardar en DB
    save_to_db(df_new)

    print("✅ Datos guardados en SQLite (inventario.db)")


# -----------------------------
# EJECUCIÓN
# -----------------------------
if __name__ == "__main__":
    scrape_and_save()
