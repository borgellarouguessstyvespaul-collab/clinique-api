from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Importe la configuration de la base de données et les modèles créés
from database import engine, get_db
import models

# Crée les tables dans la base de données (si elles n'existent pas déjà)
models.Base.metadata.create_all(bind=engine)

# Initialise l'application FastAPI
app = FastAPI(title="API Clinique")

# Route de base pour vérifier si l'API fonctionne
@app.get("/")
def accueil():
    return {"message": "Bienvenue sur l'API de la Clinique ! L'application fonctionne correctement."}

# ======== ROUTES POUR LES MEDECINS ========

# 1. Récupérer la liste des médecins
@app.get("/medecins")
def lister_medecins(db: Session = Depends(get_db)):
    medecins = db.query(models.Medecin).all()
    return medecins

# Schéma Pydantic pour lire les données envoyées par l'utilisateur
class MedecinCreate(BaseModel):
    nom: str
    prenom: str
    specialite: str

# 2. Ajouter un nouveau médecin dans la base de données
@app.post("/medecins")
def creer_medecin(medecin: MedecinCreate, db: Session = Depends(get_db)):
    nouveau_medecin = models.Medecin(
        nom=medecin.nom,
        prenom=medecin.prenom,
        specialite=medecin.specialite
    )
    db.add(nouveau_medecin)
    db.commit()
    db.refresh(nouveau_medecin)
    return nouveau_medecin
