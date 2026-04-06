from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

# Importe la configuration de la base de données et les modèles créés
from database import engine, get_db
import models

# Crée les tables dans la base de données (si elles n'existent pas déjà)
models.Base.metadata.create_all(bind=engine)

# Initialise l'application FastAPI
app = FastAPI(
    title="API Clinique",
    description="Une API professionnelle pour gérer une clinique avec des patients, médecins et consultations.",
    version="1.0.0"
)

# Configuration CORS pour permettre aux applications front-end (React, Vue, mobile) de communiquer avec l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En production, mettez l'URL de votre site web
    allow_credentials=True,
    allow_methods=["*"], # Permet toutes les méthodes (GET, POST, PUT, DELETE)
    allow_headers=["*"], # Permet tous les headers
)

# Route de base
@app.get("/", tags=["Accueil"])
def accueil():
    return {"message": "Bienvenue sur l'API de la Clinique ! L'application fonctionne correctement."}


# ======== SCHÉMAS ET ROUTES POUR LES MEDECINS ========

class MedecinCreate(BaseModel):
    nom: str
    prenom: str
    specialite: str
    
class MedecinResponse(MedecinCreate):
    id: int
    class Config:
        from_attributes = True

@app.get("/medecins", response_model=List[MedecinResponse], tags=["Médecins"])
def lister_medecins(db: Session = Depends(get_db)):
    """Affiche la liste de tous les médecins de la clinique."""
    medecins = db.query(models.Medecin).all()
    return medecins

@app.get("/medecins/{medecin_id}", response_model=MedecinResponse, tags=["Médecins"])
def voir_medecin(medecin_id: int, db: Session = Depends(get_db)):
    """Recherche un médecin spécifique par son ID."""
    medecin = db.query(models.Medecin).filter(models.Medecin.id == medecin_id).first()
    if not medecin:
        raise HTTPException(status_code=404, detail="Médecin non trouvé")
    return medecin

@app.post("/medecins", response_model=MedecinResponse, status_code=status.HTTP_201_CREATED, tags=["Médecins"])
def creer_medecin(medecin: MedecinCreate, db: Session = Depends(get_db)):
    """Ajoute un nouveau médecin dans la base de données."""
    nouveau_medecin = models.Medecin(**medecin.model_dump())
    db.add(nouveau_medecin)
    db.commit()
    db.refresh(nouveau_medecin)
    return nouveau_medecin


# ======== SCHÉMAS ET ROUTES POUR LES PATIENTS ========

class PatientCreate(BaseModel):
    nom: str
    prenom: str
    date_naissance: str # Ex: "1990-05-15"

class PatientResponse(PatientCreate):
    id: int
    class Config:
        from_attributes = True

@app.get("/patients", response_model=List[PatientResponse], tags=["Patients"])
def lister_patients(db: Session = Depends(get_db)):
    """Affiche la liste de tous les patients."""
    patients = db.query(models.Patient).all()
    return patients

@app.get("/patients/{patient_id}", response_model=PatientResponse, tags=["Patients"])
def voir_patient(patient_id: int, db: Session = Depends(get_db)):
    """Recherche un patient spécifique par son ID."""
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouvé")
    return patient

@app.post("/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED, tags=["Patients"])
def creer_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    """Inscrit un nouveau patient à la clinique."""
    nouveau_patient = models.Patient(**patient.model_dump())
    db.add(nouveau_patient)
    db.commit()
    db.refresh(nouveau_patient)
    return nouveau_patient


# ======== SCHÉMAS ET ROUTES POUR LES DOSSIERS MÉDICAUX ========

class DossierMedicalCreate(BaseModel):
    groupe_sanguin: str
    antecedents: Optional[str] = None
    allergies: Optional[str] = None
    patient_id: int
    
class DossierMedicalResponse(DossierMedicalCreate):
    id: int
    class Config:
        from_attributes = True

@app.get("/dossiers", response_model=List[DossierMedicalResponse], tags=["Dossiers Médicaux"])
def lister_dossiers(db: Session = Depends(get_db)):
    """Affiche tous les dossiers médicaux existants."""
    return db.query(models.DossierMedical).all()

@app.get("/dossiers/{dossier_id}", response_model=DossierMedicalResponse, tags=["Dossiers Médicaux"])
def voir_dossier(dossier_id: int, db: Session = Depends(get_db)):
    """Cherche un dossier médical spécifique selon son ID."""
    dossier = db.query(models.DossierMedical).filter(models.DossierMedical.id == dossier_id).first()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier médical non trouvé")
    return dossier

@app.post("/dossiers", response_model=DossierMedicalResponse, status_code=status.HTTP_201_CREATED, tags=["Dossiers Médicaux"])
def creer_dossier(dossier: DossierMedicalCreate, db: Session = Depends(get_db)):
    """Ouvre un nouveau dossier médical pour un patient."""
    nouveau_dossier = models.DossierMedical(**dossier.model_dump())
    db.add(nouveau_dossier)
    db.commit()
    db.refresh(nouveau_dossier)
    return nouveau_dossier


# ======== SCHÉMAS ET ROUTES POUR LES CONSULTATIONS ========

class ConsultationCreate(BaseModel):
    date: str
    motif: str
    diagnostic: Optional[str] = None
    patient_id: int
    medecin_id: int

class ConsultationResponse(ConsultationCreate):
    id: int
    class Config:
        from_attributes = True

@app.get("/consultations", response_model=List[ConsultationResponse], tags=["Consultations"])
def lister_consultations(db: Session = Depends(get_db)):
    """Historique de toutes les consultations de la clinique."""
    return db.query(models.Consultation).all()

@app.post("/consultations", response_model=ConsultationResponse, status_code=status.HTTP_201_CREATED, tags=["Consultations"])
def creer_consultation(consultation: ConsultationCreate, db: Session = Depends(get_db)):
    """Enregistre une nouvelle consultation entre un patient et un médecin."""
    nouvelle_consultation = models.Consultation(**consultation.model_dump())
    db.add(nouvelle_consultation)
    db.commit()
    db.refresh(nouvelle_consultation)
    return nouvelle_consultation


# ======== SCHÉMAS ET ROUTES POUR LES MEDICAMENTS ========

class MedicamentCreate(BaseModel):
    nom: str
    dosage: str

class MedicamentResponse(MedicamentCreate):
    id: int
    class Config:
        from_attributes = True

@app.get("/medicaments", response_model=List[MedicamentResponse], tags=["Médicaments"])
def lister_medicaments(db: Session = Depends(get_db)):
    """Liste de tous les médicaments disponibles."""
    return db.query(models.Medicament).all()

@app.post("/medicaments", response_model=MedicamentResponse, status_code=status.HTTP_201_CREATED, tags=["Médicaments"])
def creer_medicament(medicament: MedicamentCreate, db: Session = Depends(get_db)):
    """Ajoute un nouveau médicament dans le système."""
    nouveau_medicament = models.Medicament(**medicament.model_dump())
    db.add(nouveau_medicament)
    db.commit()
    db.refresh(nouveau_medicament)
    return nouveau_medicament
