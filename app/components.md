## Componentes principais do projeto

A tabela abaixo resume os componentes essenciais do sistema, o seu tipo e onde se encontram implementados.

| Componente         | Tipo           | Localização / Tecnologia           |
|--------------------|----------------|----------------------------------|
| main.py            | API Backend    | FastAPI                          |
| create_event.py    | UI Module      | Streamlit                       |
| Firebase           | Auth/Storage   | Firebase Auth + Firestore       |
| Imgur / Cloudinary | Image Hosting  | API externa (upload de imagem)  |
| requirements.txt   | Dependency list| Python pip environment           |
