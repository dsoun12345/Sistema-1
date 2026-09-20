from conexion import supabase

try:
    resultado = supabase.table("productos").select("*").execute()
    print("✅ Conexión exitosa!")
    print("Productos encontrados:", len(resultado.data))
    print(resultado.data)
except Exception as e:
    print("❌ Error de conexión:", e)