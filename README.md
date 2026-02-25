RUN THE APPLICATION (DOCKER)

1) Prerequisites

Install Docker Desktop:
https://www.docker.com/products/docker-desktop

No need to install Python, Node.js, or any other dependencies manually.



2) Clone the Repository

If using Git:

git clone https://github.com/Gusrules/Diplomatiki.git

cd Diplomatiki

Alternatively, download the repository as a ZIP file and open the project folder.



3) Start the Application

From the project root folder, run:

docker compose up --build

The first run may take a few minutes, as Docker images will be downloaded and built.



4) Access the Application

Frontend:
http://localhost:3001

Backend API (Swagger documentation):
http://localhost:8000/docs



5) Stop the Application

To stop the application, press:

Ctrl + C

Or run:

docker compose down


-----------------------------

Database

The application uses SQLite.

The database file:
app.db

It is automatically mounted inside the Docker container.

-----------------------------------

Notes

If port 3001 is already in use, change it in docker-compose.yml.

If you modify the source code, rebuild the containers with:

docker compose up --build
