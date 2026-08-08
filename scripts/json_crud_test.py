import requests

B = "http://127.0.0.1:8000"

# Crear
r = requests.post(B + "/api/projects", json={
    "name": "JSON Test",
    "destination": "Cusco",
    "template": "cinco-datos",
    "format": "square",
    "cards": [
        {"type": "cinco_datos", "title": "Cinco datos", "facts": ["a", "b", "c", "d", "e"]},
        {"type": "mito_realidad", "title": "Mito", "myth": "m", "reality": "r"},
    ],
})
p = r.json()
pid = p["id"]
print("creado:", pid[:8], "| cards:", len(p["cards"]))

# Listar
print("listar:", len(requests.get(B + "/api/projects").json()), "proyectos")

# Obtener
g = requests.get(B + f"/api/projects/{pid}").json()
print("obtener:", g["name"], "| card0 title:", g["cards"][0]["title"])

# Actualizar
r = requests.put(B + f"/api/projects/{pid}", json={
    "name": "JSON Test Editado",
    "cards": [{"type": "dato_curioso", "title": "Nuevo titulo"}],
})
print("actualizar:", r.json()["name"], "| cards:", len(r.json()["cards"]))

# Eliminar
print("eliminar:", requests.delete(B + f"/api/projects/{pid}").status_code)
print("listar tras borrar:", len(requests.get(B + "/api/projects").json()), "proyectos")
