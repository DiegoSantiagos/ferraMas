import json
from django.shortcuts import redirect, render
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from ferraMas.settings import MEDIA_URL
import requests
import os
from django.shortcuts import render

def get_context_with_sedes():
    sedes = obtener_sedes()
    return {'sedes': sedes or []}

def filtrarProductosPorSede(sede_id):
    try:
        todos_productos = obtenerProductos()
        print(f"Filtrando por sede_id: {sede_id}")
        for p in todos_productos:
            print(f"Producto: {p['idproducto']} idsede: {p.get('idsede')}")
        if not todos_productos:
            return []
        productos_filtrados = [
            producto for producto in todos_productos 
            if str(producto.get('idsede', '')) == str(sede_id)
        ]
        print(f"Productos filtrados para sede {sede_id}: {len(productos_filtrados)}")
        return productos_filtrados
    except Exception as e:
        print(f"Error filtrando productos por sede: {e}")
        return []

def obtenerProductosPorSede(sede_id):
    try:
        url = f"http://localhost:8089/api/productos/sedes/{sede_id}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(f"Productos por sede {sede_id}: {len(data) if data else 0}")
            return data
        else:
            print(f"Endpoint /api/productos/sedes/{sede_id} no disponible, filtrando localmente")
            return filtrarProductosPorSede(sede_id)
    except Exception as e:
        print(f"Error obteniendo productos por sede {sede_id}: {e}")
        return filtrarProductosPorSede(sede_id)

def ver_home(request):
    context = get_context_with_sedes()
    # Agregar productos filtrados por sede para mostrar en home
    sede_seleccionada = request.session.get('sede_seleccionada')
    if sede_seleccionada:
        productos_destacados = obtenerProductosPorSede(sede_seleccionada)
        context['productos_destacados'] = productos_destacados[:6] if productos_destacados else []
    context['MEDIA_URL'] = MEDIA_URL
    return render(request, 'verHome.html', context) 

def obtener_empleados():
    url="http://localhost:8089/api/empleados/"
    try:
        response = requests.get(url)
        data=response.json()
        return data
    except Exception as e:
        return None
    
def ver_empleados(request):
    context = get_context_with_sedes()
    empleados = obtener_empleados()
    context['datos'] = empleados
    return render(request, 'ver_empleados.html', context)

def obtener_comunas():
    url="http://localhost:8089/api/comunas/"
    try:
        response = requests.get(url)
        data=response.json()
        return data
    except Exception as e:
        return None
    
def ver_comunas(request):
    comunas = obtener_comunas()
    context = {'datos': comunas}
    return render(request, 'ver_comunas.html', context)

def obtenerCatalogo():
    try:
        url = "http://localhost:8089/api/productos/"
        response = requests.get(url)
        data = response.json()
        return data
    except Exception as e:
        return None

def verCatalogo(request):
    context = get_context_with_sedes()
    mostrando_todos = False

    # Botón "Ver todos los productos"
    if request.method == 'POST' and request.POST.get('ver_todos') == '1':
        request.session['mostrando_todos'] = True

    # Botón "Ver productos filtrados"
    elif request.method == 'POST' and request.POST.get('ver_filtro') == '1':
        request.session['mostrando_todos'] = False

    mostrando_todos = request.session.get('mostrando_todos', False)
    sede_seleccionada = request.session.get('sede_seleccionada')

    if sede_seleccionada and not mostrando_todos:
        productos = obtenerProductosPorSede(sede_seleccionada)
        sede_nombre = request.session.get('sede_nombre', 'Sede seleccionada')
        context['sede_filtro'] = {
            'id': sede_seleccionada,
            'nombre': sede_nombre
        }
    else:
        productos = obtenerProductos()
        if sede_seleccionada:
            sede_nombre = request.session.get('sede_nombre', 'Sede seleccionada')
            context['sede_filtro'] = {
                'id': sede_seleccionada,
                'nombre': sede_nombre
            }

    if productos:
        for producto in productos:
            imagenes = obtenerImagenesProducto(producto['idproducto'])
            producto['imagenes'] = imagenes
            if imagenes and len(imagenes) > 0:
                producto['imagen_url'] = f"{MEDIA_URL}{imagenes[0]['imagen']}"
                producto['tiene_imagen_api'] = True
            else:
                producto['imagen_url'] = obtener_imagen_estatica(producto['idproducto'])
                producto['tiene_imagen_api'] = False

    context['datos'] = productos
    context['MEDIA_URL'] = MEDIA_URL
    return render(request, 'ver_Catalogo.html', context)

def obtener_imagen_estatica(producto_id):
    imagenes_estaticas = {
        'MART001': 'martillo_carpintero.jpg',
        'DEST001': 'destornillador.jpg', 
        'TALA001': 'taladro_electrico.jpg',
        'CLAV001': 'clavos_construccion.jpg',
        'TORN001': 'tornillos_madera.jpg',
        'CEME001': 'cemento_portland.jpg',
        'CABL001': 'cable_electrico.jpg',
        'ENCH001': 'enchufe_schuko.jpg'
    }
    
    if producto_id in imagenes_estaticas:
        return f"{MEDIA_URL}{imagenes_estaticas[producto_id]}"
    else:
        return None

def obtenerProductos():
    try:
        url = "http://localhost:8089/api/productos/"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Procesar imágenes para cada producto
        if data:
            for producto in data:
                imagenes = obtenerImagenesProducto(producto['idproducto'])
                producto['imagenes'] = imagenes
                
                # Determinar imagen a usar
                if imagenes and len(imagenes) > 0:
                    producto['imagen_url'] = f"{MEDIA_URL}{imagenes[0]['imagen']}"
                    producto['tiene_imagen_api'] = True
                    producto['descripcion'] = imagenes[0].get('descripcion', '')
                else:
                    producto['imagen_url'] = obtener_imagen_estatica(producto['idproducto'])
                    producto['tiene_imagen_api'] = False
                    producto['descripcion'] = ''
        
        print(f"API Response: {len(data)} productos procesados")
        return data
    except Exception as e:
        print(f"Error obteniendo productos: {e}")
        return []
    
def verProductos(request):
    context = get_context_with_sedes()
    productos = obtenerProductos()
    context = {'datos': productos}
    return render(request, 'ver_producto.html', context)

def obtenerProductoPorId(producto_id):
    try:
        url = f"http://localhost:8089/api/productos/{producto_id}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        print(f"API Response for product {producto_id}: {data}")
        return data
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"Producto con ID {producto_id} no encontrado")
            return None
        print(f"Error HTTP: {e}")
        return None
    except Exception as e:
        print(f"Error obteniendo producto {producto_id}: {e}")
        return None

def verProductoDetalle(request, producto_id):
    producto = obtenerProductoPorId(producto_id)
    if producto is None:
        return render(request, 'producto_no_encontrado.html', {'producto_id': producto_id})
    
    # Forzamos el nombre de la imagen
    producto['imagen'] = f"{producto_id.lower()}.jpg"
    print("Nombre de imagen:", producto['imagen'])  # Para depuración
    
    return render(request, 'ver_producto_detalle.html', {'producto': producto})

def obtener_sedes():
    url="http://localhost:8089/api/sedes/"
    try:
        response = requests.get(url)
        data=response.json()
        return data
    except Exception as e:
        return None

def ver_sedes(request):
    sedes = obtener_sedes()
    context = get_context_with_sedes()
    context['datos'] = context['sedes']
    return render(request, 'ver_sedes.html', context)

def seleccionar_sede(request):
    if request.method == 'POST':
        sede_id = request.POST.get('sede_id')
        request.session['sede_seleccionada'] = sede_id
        return redirect('home')
    
    sedes = obtener_sedes()
    context = {'sedes': sedes}
    return render(request, 'seleccionar_sede.html', context)

def cambiar_sede_ajax(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            sede_id = data.get('sede_id')
            
            if sede_id:
                sedes = obtener_sedes()
                sede_seleccionada = None
                
                for sede in sedes:
                    if str(sede['idsede']) == str(sede_id):
                        sede_seleccionada = sede
                        break
                
                if sede_seleccionada:
                    request.session['sede_seleccionada'] = sede_id
                    request.session['sede_nombre'] = sede_seleccionada['nombresede']
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Sede cambiada a {sede_seleccionada["nombresede"]}',
                        'sede_nombre': sede_seleccionada['nombresede']
                    })
                else:
                    return JsonResponse({'success': False, 'message': 'Sede no encontrada'})
            else:
                return JsonResponse({'success': False, 'message': 'ID de sede no válido'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'Error al cambiar sede'})
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

def lista_productos(request):
    context = get_context_with_sedes()
    productos = obtenerProductos()
    context['datos'] = productos or []
    context['MEDIA_URL'] = MEDIA_URL
    return render(request, 'admins/lista_productos.html', context)

def obtenerImagenesProducto(producto_id):
    try:
        url = f"http://localhost:8089/api/imagenes-producto/producto/{producto_id}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(f"Imágenes para producto {producto_id}: {len(data) if data else 0}")
            return data
        else:
            print(f"No se encontraron imágenes para producto {producto_id}")
            return []
    except Exception as e:
        print(f"Error obteniendo imágenes del producto {producto_id}: {e}")
        return []

def verProductoDetalle(request, producto_id):
    producto = obtenerProductoPorId(producto_id)
    if producto is None:
        return render(request, 'producto_no_encontrado.html', {'producto_id': producto_id})
    
    # Obtener imágenes del producto
    imagenes = obtenerImagenesProducto(producto_id)
    producto['imagenes'] = imagenes
    
    # Determinar imagen principal
    if imagenes and len(imagenes) > 0:
        producto['imagen_url'] = f"{MEDIA_URL}{imagenes[0]['imagen']}"
        producto['tiene_imagen_api'] = True
        producto['descripcion'] = imagenes[0].get('descripcion', '')
    else:
        producto['imagen_url'] = obtener_imagen_estatica(producto_id)
        producto['tiene_imagen_api'] = False
        producto['descripcion'] = ""
    return render(request, 'ver_producto_detalle.html', {'producto': producto})

def anadirProducto(request):
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre')
            precio = float(request.POST.get('precio', 0))
            stockminimo = int(request.POST.get('stockminimo', 0))
            idcategoria = int(request.POST.get('idcategoria'))
            idsede = int(request.POST.get('idsede'))

            producto_data = {
                'nombre': nombre,
                'precio': precio,
                'stockminimo': stockminimo,
                'idcategoria': idcategoria,
                'idsede': idsede,
            }

            url = "http://localhost:8089/api/productos/"
            response = requests.post(url, json=producto_data)

            if response.status_code == 201:
                producto_creado = response.json()

                # Si hay imagen, guarda el archivo en media y manda solo el nombre a la API
                if 'imagen' in request.FILES:
                    imagen_file = request.FILES['imagen']
                    descripcion = request.POST.get('descripcion', '')

                    # Guardar la imagen en la carpeta media
                    media_path = os.path.join(settings.MEDIA_ROOT, imagen_file.name)
                    with open(media_path, 'wb+') as destination:
                        for chunk in imagen_file.chunks():
                            destination.write(chunk)

                    # Mandar solo el nombre del archivo a la API de imágenes
                    imagen_data = {
                        'idproducto': producto_creado['idproducto'],
                        'imagen': imagen_file.name,
                        'descripcion': descripcion
                    }
                    url_imagen = "http://localhost:8089/api/imagenes-producto/"
                    requests.post(url_imagen, json=imagen_data)

                return JsonResponse({
                    'success': True,
                    'message': 'Producto añadido exitosamente',
                    'producto_id': producto_creado['idproducto']
                })
            else:
                return JsonResponse({'success': False, 'message': 'Error al añadir producto'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

def ver_anadir_producto(request):
    context = get_context_with_sedes()
    
    # Obtener categorías para el formulario
    try:
        url_categorias = "http://localhost:8089/api/categorias/"
        response = requests.get(url_categorias)
        if response.status_code == 200:
            context['categorias'] = response.json()
        else:
            context['categorias'] = []
    except Exception as e:
        context['categorias'] = []
    
    return render(request, 'admins/anadir_producto.html', context)

def ver_modificar_producto(request, producto_id):
    context = get_context_with_sedes()
    producto = obtenerProductoPorId(producto_id)
    if not producto:
        return render(request, 'producto_no_encontrado.html', {'producto_id': producto_id})

    if producto.get('idcategoria'):
        producto['idcategoria'] = int(producto['idcategoria'])
    if producto.get('idsede'):
        producto['idsede'] = int(producto['idsede'])

    # Obtener la imagen principal y su descripción
    imagenes = obtenerImagenesProducto(producto_id)
    if imagenes and len(imagenes) > 0:
        context['descripcion'] = imagenes[0].get('descripcion', '')
    else:
        context['descripcion'] = ''

    try:
        url_categorias = "http://localhost:8089/api/categorias/"
        response = requests.get(url_categorias)
        if response.status_code == 200:
            categorias = response.json()
            print("CATEGORIAS API:", categorias)  # <-- Agrega esto
            # Forzar idcategoria a int si existe
            for cat in categorias:
                if 'idcategoria' in cat and cat['idcategoria']:
                    cat['idcategoria'] = int(cat['idcategoria'])
            context['categorias'] = categorias
        else:
            context['categorias'] = []
    except Exception as e:
        context['categorias'] = []

    context['producto'] = producto
    return render(request, 'admins/anadir_producto.html', context)

def modificarProducto(request, producto_id):
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre = request.POST.get('nombre')
            precio = float(request.POST.get('precio', 0))
            stockminimo = int(request.POST.get('stockminimo', 0))
            idcategoria = int(request.POST.get('idcategoria'))
            idsede = int(request.POST.get('idsede'))
            descripcion = request.POST.get('descripcion', '')
            
            # Crear el producto actualizado
            producto_data = {
                'idproducto': producto_id,
                'nombre': nombre,
                'precio': precio,
                'stockminimo': stockminimo,
                'idcategoria': idcategoria,
                'idsede': idsede,
                'descripcion': descripcion
            }
            
            # Manejar archivo de imagen si se subió
            if 'imagen' in request.FILES:
                imagen_file = request.FILES['imagen']
                imagen_data = {
                    'idproducto': producto_id,
                    'imagen': imagen_file.name,
                    'descripcion': descripcion
                }
                
                # Actualizar imagen
                url_imagen = f"http://localhost:8089/api/imagenes-producto/producto/{producto_id}"
                requests.put(url_imagen, json=imagen_data)
            
            # Enviar actualización del producto a la API
            url = f"http://localhost:8089/api/productos/{producto_id}"
            response = requests.put(url, json=producto_data)
            
            if response.status_code == 200:
                return JsonResponse({'success': True, 'message': 'Producto modificado exitosamente'})
            else:
                return JsonResponse({'success': False, 'message': 'Error al modificar producto'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

def eliminarProducto(request, producto_id):
    if request.method == 'POST':
        try:
            # Primero eliminar imágenes asociadas
            # Verificar si el producto tiene imágenes antes de intentar eliminarlas
            imagenes = obtenerImagenesProducto(producto_id)
            if imagenes and len(imagenes) > 0:
                try:
                    url_imagenes = f"http://localhost:8089/api/imagenes-producto/producto/{producto_id}"
                    requests.delete(url_imagenes)
                except Exception:
                    pass  # Continuar aunque falle la eliminación de imágenes
            
            # Enviar solicitud DELETE a la API
            url = f"http://localhost:8089/api/productos/{producto_id}"
            response = requests.delete(url)
            
            if response.status_code == 204 or response.status_code == 200:
                return JsonResponse({'success': True, 'message': 'Producto eliminado exitosamente'})
            else:
                return JsonResponse({'success': False, 'message': 'Error al eliminar producto'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

def lista_sedes(request):
    return render(request, 'ver_sedes.html')

def ver_clientes(request):
    try:
        url = "http://localhost:8089/api/clientes/"
        response = requests.get(url)
        if response.status_code == 200:
            clientes = response.json()
        else:
            clientes = []
    except Exception as e:
        clientes = []
    return render(request, 'admins/lista_clientes.html', {'clientes': clientes})
