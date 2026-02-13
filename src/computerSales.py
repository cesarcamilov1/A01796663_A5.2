import json
import sys
import time


def load_json_file(filepath):
    """Lee un archivo JSON y devuelve su contenido."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: No se encontró '{filepath}'.")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Error: '{filepath}' no es JSON válido.", e.doc, e.pos
        )


def validate_price_catalogue(catalogue):
    """Recorre el catálogo y armamos un diccionario {producto: precio}."""
    prices = {}
    if not isinstance(catalogue, list):
        print("Error: El catálogo no tiene el formato esperado, debe ser una lista.")
        return prices

    for i, item in enumerate(catalogue):
        if not isinstance(item, dict):
            print(f"El elemento {i} del catálogo no es válido.")
            continue
        if 'name' not in item or 'price' not in item:
            print(f"Al elemento {i} le falta 'name' o 'price'.")
            continue

        nombre = item['name']
        try:
            precio = float(item['price'])
        except (ValueError, TypeError) as e:
            print(f"No se pudo leer precio del elemento {i}: {e}")
            continue

        if precio < 0:
            print(f"Precio negativo para '{nombre}', se omite.")
            continue

        prices[nombre] = precio

    return prices


def process_sales(sales_data, price_catalogue):
    """
    Recorremos las ventas, buscando cada producto en el catálogo
    y sumando los totales.
    """
    total = 0.0
    results = []
    errors = []

    if not isinstance(sales_data, list):
        errors.append("Los datos de ventas no son una lista.")
        return total, results, errors

    for idx, sale in enumerate(sales_data):
        if not isinstance(sale, dict):
            errors.append(f"Venta {idx}: no es un diccionario válido.")
            continue

        if 'Sale' not in sale:
            errors.append(f"Venta {idx}: falta el campo 'Sale'.")
            continue

        sale_id = sale['Sale']
        items = sale.get('items', [])
        if not isinstance(items, list):
            errors.append(f"{sale_id}: 'items' no es una lista.")
            continue

        sale_total = 0.0
        sale_det = {'sale_id': sale_id, 'items': [], 'total': 0.0}

        for j, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"{sale_id}, item {j}: formato inválido.")
                continue

            product = item.get('Product')
            qty = item.get('Quantity', 0)

            if not product:
                errors.append(f"{sale_id}, item {j}: falta 'Product'.")
                continue

            if product not in price_catalogue:
                errors.append(
                    f"{sale_id}: '{product}' no está en el catálogo."
                )
                continue

            # Validamos la cantidad
            try:
                qty = int(qty)
            except (ValueError, TypeError):
                errors.append(f"{sale_id}: cantidad inválida para '{product}'.")
                continue

            if qty < 0:
                errors.append(
                    f"{sale_id}: cantidad negativa para '{product}'."
                )
                continue

            precio = price_catalogue[product]
            subtotal = qty * precio
            sale_total += subtotal

            sale_det['items'].append({
                'product': product,
                'quantity': qty,
                'price': precio,
                'subtotal': subtotal
            })

        sale_det['total'] = sale_total
        total += sale_total
        results.append(sale_det)

    return total, results, errors


def format_results(total_sales, detailed_results, errors, elapsed):
    """String del reporte con formato de tabla."""
    lines = []
    sep = "=" * 70

    lines.append(sep)
    lines.append("REPORTE DE VENTAS")
    lines.append(sep)
    lines.append("")

    for sale in detailed_results:
        lines.append(f"Venta: {sale['sale_id']}")
        lines.append("-" * 70)
        for it in sale['items']:
            lines.append(
                f"  {it['product']:30s} | "
                f"Cant: {it['quantity']:4d} | "
                f"Precio: ${it['price']:8.2f} | "
                f"Subtotal: ${it['subtotal']:10.2f}"
            )
        lines.append(f"  {'TOTAL VENTA':47s} ${sale['total']:10.2f}")
        lines.append("")

    # Resumen
    lines.append(sep)
    lines.append("RESUMEN")
    lines.append(sep)
    lines.append(f"Total de ventas: {len(detailed_results)}")
    lines.append(f"TOTAL GENERAL: ${total_sales:,.2f}")
    lines.append("")

    if errors:
        lines.append(sep)
        lines.append("ERRORES ENCONTRADOS")
        lines.append(sep)
        for err in errors:
            lines.append(f"  - {err}")
        lines.append("")

    lines.append(sep)
    lines.append(f"Tiempo de ejecución: {elapsed:.4f} segundos")
    lines.append(sep)

    return "\n".join(lines)


def save_results(text, filename="SalesResults.txt"):
    """Guarda el reporte en un txt."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"\nResultados guardados en: {filename}")
    except IOError as e:
        print(f"Error al guardar el archivo: {e}")


def main():
    # revisamos argumentos para asegurarnos que se haga correctamente
    if len(sys.argv) != 3:
        print("Uso: python computerSales.py priceCatalogue.json salesRecord.json")
        sys.exit(1)

    catalogo_path = sys.argv[1]
    ventas_path = sys.argv[2]

    start = time.time()

    try:
        # Leemos lo json
        print("Cargando catálogo de precios...")
        catalogo_raw = load_json_file(catalogo_path)
        # cargamos las ventas
        ventas_raw = load_json_file(ventas_path)
        # se arma el cataglogo de precios, validando que tenga el formato correcto
        precios = validate_price_catalogue(catalogo_raw)
        if not precios:
            print("Error: No se encontraron productos válidos en el catálogo.")
            sys.exit(1)
        print(f"Productos cargados: {len(precios)}")

        # Calcular ventas
        print("Procesando ventas...")
        total, detalle, errores = process_sales(ventas_raw, precios)

        elapsed = time.time() - start

        # Reporte de resultados
        reporte = format_results(total, detalle, errores, elapsed)
        print("\n" + reporte)

        # Se guardan los resultados
        save_results(reporte)

    except FileNotFoundError as e:
        print(f"\n{e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"\nError leyendo JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
