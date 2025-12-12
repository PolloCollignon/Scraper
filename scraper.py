import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from datetime import datetime
import os

print("El script ha iniciado correctamente.")

# Función para obtener productos desde una URL con paginación
def get_all_products():
    all_products = []
    base_url = "https://lebump.com.mx/products.json"
    page = 1
    limit = 350

    while True:
        response = requests.get(f"{base_url}?page={page}&limit={limit}")
        data = response.json()

        if not data['products']:
            break

        all_products.extend(data['products'])
        page += 1

    return all_products

# Función para extraer inventario de un producto
def extract_inventory(product_url, product_data):
    try:
        product_page = requests.get(product_url)
        soup = BeautifulSoup(product_page.text, 'html.parser')

        script_tag = soup.find('script', {
            'type': 'application/json',
            'data-product-inventory-json': True
        })

        if script_tag:
            inventory_data = json.loads(script_tag.string)

            for key, value in inventory_data['inventory'].items():
                inventory_id = key
                inventory_quantity = value.get('inventory_quantity', 'N/A')
                product_data.append({
                    'product_url': product_url,
                    'inventory_id': inventory_id,
                    'inventory_quantity': inventory_quantity
                })
    except Exception as e:
        print(f"Error al procesar {product_url}: {e}")

# Función principal para realizar scraping y guardar Excel
def scrape_and_save_excel():
    product_data = []

    products = get_all_products()

    for product in products:
        handle = product['handle']
        product_url = f"https://lebump.com.mx/products/{handle}"
        extract_inventory(product_url, product_data)

    df_new = pd.DataFrame(product_data)

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    file_name = f"inventario_lebump_{timestamp}.xlsx"

    # Guardar en carpeta actual (GitHub Actions lo subirá como artifact)
    output_path = os.path.join(file_name)
    df_new.to_excel(output_path, index=False)

    print(f"Datos guardados en {output_path}")

if __name__ == "__main__":
    scrape_and_save_excel()
