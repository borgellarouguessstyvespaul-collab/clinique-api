from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

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

class MedecinCreate(BaseModel):
    nom: str
    prenom: str
    specialite: str

@app.get("/medecins")
def lister_medecins(db: Session = Depends(get_db)):
    medecins = db.query(models.Medecin).all()
    return medecins

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

# ======== ROUTES POUR LES PATIENTS ========

class PatientCreate(BaseModel):
    nom: str
    prenom: str
    date_naissance: str # Ex: "1990-05-15"

@app.post("/patients")
def creer_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    nouveau_patient = models.Patient(
        nom=patient.nom,
        prenom=patient.prenom,
        date_naissance=patient.date_naissance
    )
    db.add(nouveau_patient)
    db.commit()
    db.refresh(nouveau_patient)
    return nouveau_patient

@app.get("/patients")
def lister_patients(db: Session = Depends(get_db)):
    patients = db.query(models.Patient).all()
    return patients

# ======== ROUTES POUR LES DOSSIERS MÉDICAUX ========

class DossierMedicalCreate(BaseModel):
    groupe_sanguin: str
    antecedents: Optional[str] = None
    allergies: Optional[str] = None
    patient_id: int

@app.post("/dossiers")
def creer_dossier(dossier: DossierMedicalCreate, db: Session = Depends(get_db)):
    nouveau_dossier = models.DossierMedical(
        groupe_sanguin=dossier.groupe_sanguin,
        antecedents=dossier.antecedents,
        allergies=dossier.allergies,
        patient_id=dossier.patient_id
    )
    db.add(nouveau_dossier)
    db.commit()
    db.refresh(nouveau_dossier)
    return nouveau_dossier

@app.get("/dossiers")
def lister_dossiers(db: Session = Depends(get_db)):
    return db.query(models.DossierMedical).all()

# ======== ROUTES POUR LES CONSULTATIONS ========

class ConsultationCreate(BaseModel):
    date: str
    motif: str
    diagnostic: Optional[str] = None
    patient_id: int
    medecin_id: int

@app.post("/consultations")
def creer_consultation(consultation: ConsultationCreate, db: Session = Depends(get_db)):
    nouvelle_consultation = models.Consultation(
        date=consultation.date,
        motif=consultation.motif,
        diagnostic=consultation.diagnostic,
        patient_id=consultation.patient_id,
        medecin_id=consultation.medecin_id
    )
    db.add(nouvelle_consultation)
    db.commit()
    db.refresh(nouvelle_consultation)
    return nouvelle_consultation

@app.get("/consultations")
def lister_consultations(db: Session = Depends(get_db)):
    return db.query(models.Consultation).all()

# ======== ROUTES POUR LES MEDICAMENTS ========

class MedicamentCreate(BaseModel):
    nom: str
    dosage: str

@app.post("/medicaments")
def creer_medicament(medicament: MedicamentCreate, db: Session = Depends(get_db)):
    nouveau_medicament = models.Medicament(
        nom=medicament.nom,
        dosage=medicament.dosage
    )
    db.add(nouveau_medicament)
    db.commit()
    db.refresh(nouveau_medicament)
    return nouveau_medicament

@app.get("/medicaments")
def lister_medicaments(db: Session = Depends(get_db)):
    return db.query(models.Medicament).all()
