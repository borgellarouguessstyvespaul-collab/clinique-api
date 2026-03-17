# =====================================================
# schemas.py — Schémas Pydantic pour valider les données
# Pydantic vérifie les données AVANT qu'elles entrent en base
# Si une donnée manque ou a un mauvais type, Pydantic retourne
# automatiquement une erreur 422 Unprocessable Entity
# =====================================================

### ─── IMPORTATIONS ────────────────────────────────────
# permet de créer des modèles Pydantic pour valider le corps des requêtes HTTP
from pydantic import BaseModel
# Optional = champ peut être vide (None) ; List = une liste d'objets
from typing import Optional, List


# =====================================================
### ─── SCHÉMAS MÉDECIN ──────────────────────────────
# 3 classes pour gérer les données médecin : Base, Create, Out
# Modèle en cascade : Base → Create (POST) et Out (réponse GET)
# =====================================================

## MedecinBase — champs communs à tous les schémas Médecin
# Pydantic vérifie que nom, prenom, specialite sont des str obligatoires
class MedecinBase(BaseModel):
    nom:        str  # nom du médecin — obligatoire, ne peut pas être vide
    prenom:     str  # prénom du médecin — obligatoire
    specialite: str  # spécialité (ex : "Pédiatrie") — obligatoire

## MedecinCreate — schéma pour le corps du POST /medecins
# hérite de tous les champs de MedecinBase — rien de plus pour créer un médecin
class MedecinCreate(MedecinBase):
    pass  # menm champs ak MedecinBase — pa gen anyen anplis

## MedecinOut — schéma de réponse retourné par FastAPI (GET /medecins)
# ajoute l'ID de la base de données généré automatiquement
class MedecinOut(MedecinBase):
    id: int  # ID unique du médecin — généré par SQLAlchemy (auto-increment)

    class Config:
        from_attributes = True  # permet à Pydantic de lire directement les objets SQLAlchemy (mode ORM)


# =====================================================
### ─── SCHÉMAS DOSSIER MÉDICAL ──────────────────────
# Relation One-to-One : 1 Patient → 1 DossierMedical
# DossierCreate ajoute patient_id pour lier le dossier au patient
# =====================================================

## DossierBase — champs médicaux communs (sans patient_id)
class DossierBase(BaseModel):
    groupe_sanguin: str               # groupe sanguin — obligatoire (ex : "A+", "O-")
    antecedents:    Optional[str] = None  # antécédents médicaux — peut être vide (Optional)
    allergies:      Optional[str] = None  # allergies — peut être vide aussi (Optional)

## DossierCreate — schéma pour le corps du POST /dossiers
# hérite de DossierBase et ajoute patient_id pour savoir à quel patient appartient le dossier
class DossierCreate(DossierBase):
    patient_id: int  # obligatwa pou kreye dossier — lie le dossier au patient (One-to-One)

## DossierOut — schéma de réponse pour retourner le dossier avec son ID
class DossierOut(DossierBase):
    id:         int  # ID unique du dossier — généré par la base de données
    patient_id: int  # ID du patient propriétaire du dossier — illustre la relation One-to-One

    class Config:
        from_attributes = True  # permet la conversion objet SQLAlchemy → Pydantic


# =====================================================
### ─── SCHÉMAS MÉDICAMENT ───────────────────────────
# Catalogue des médicaments du système
# Relation Many-to-Many : Medicament ↔ Consultation
# =====================================================

## MedicamentBase — champs communs pour les médicaments
class MedicamentBase(BaseModel):
    nom:    str  # nom du médicament (ex : "Amoxicillin") — obligatoire
    dosage: str  # dosage (ex : "500mg 3x par jour") — obligatoire

## MedicamentCreate — schéma pour le corps du POST /medicaments
class MedicamentCreate(MedicamentBase):
    pass  # mêmes champs que MedicamentBase — rien de plus

## MedicamentOut — schéma de réponse pour retourner le médicament avec son ID
class MedicamentOut(MedicamentBase):
    id: int  # ID unique du médicament — généré par la base de données

    class Config:
        from_attributes = True  # permet à Pydantic de lire les objets SQLAlchemy directement


# =====================================================
### ─── SCHÉMAS CONSULTATION ─────────────────────────
# Relation : Patient → Consultation (One-to-Many)
#            Medecin → Consultation (One-to-Many)
#            Consultation ↔ Medicament (Many-to-Many)
# ConsultOut inclut la liste des médicaments prescrits (données imbriquées)
# =====================================================

## ConsultBase — champs communs pour les consultations
class ConsultBase(BaseModel):
    date:       str            # date de la consultation ("YYYY-MM-DD") — obligatoire
    motif:      str            # raison de la visite — obligatoire
    diagnostic: Optional[str] = None  # diagnostic du médecin — Optional (peut être vide)
    patient_id: int            # ID du patient — clé étrangère One-to-Many (obligatoire)
    medecin_id: int            # ID du médecin — clé étrangère One-to-Many (obligatoire)

## ConsultCreate — schéma pour le corps du POST /consultations
class ConsultCreate(ConsultBase):
    pass  # mêmes champs que ConsultBase — crée une consultation sans médicaments

## ConsultOut — schéma de réponse (GET /consultations/{id}) avec données imbriquées
# retourne la consultation + la liste des médicaments prescrits (Many-to-Many)
class ConsultOut(ConsultBase):
    id:          int                    # ID unique de la consultation
    medicaments: List[MedicamentOut] = []  # liste des médicaments prescrits — commence vide, SQLAlchemy la remplit

    class Config:
        from_attributes = True  # permet la conversion objet SQLAlchemy + relation Many-to-Many → Pydantic


# =====================================================
### ─── SCHÉMAS PATIENT ──────────────────────────────
# Relation : Patient → DossierMedical (One-to-One)
#            Patient → Consultation   (One-to-Many)
# PatientOut retourne des données complètes imbriquées (dossier + consultations)
# =====================================================

## PatientBase — champs communs pour les patients
class PatientBase(BaseModel):
    nom:            str  # nom du patient — obligatoire
    prenom:         str  # prénom du patient — obligatoire
    date_naissance: str  # date de naissance ("YYYY-MM-DD") — obligatoire

## PatientCreate — schéma pour le corps du POST /patients
class PatientCreate(PatientBase):
    pass  # mêmes champs que PatientBase — rien de plus pour créer un patient

## PatientOut — schéma de réponse complet (GET /patients/{id})
# inclut le dossier médical (One-to-One) et la liste des consultations (One-to-Many)
# exemple de données imbriquées (nested data) — Pydantic valide tous les niveaux
class PatientOut(PatientBase):
    id:            int                        # ID unique du patient
    dossier:       Optional[DossierOut]    = None  # dossier médical — Optional (peut ne pas encore exister)
    consultations: List[ConsultOut]        = []    # liste des consultations — vide si aucune consultation

    class Config:
        from_attributes = True  # permet à Pydantic de lire les relations SQLAlchemy (dossier, consultations) directement


# =====================================================
### ─── SCHÉMAS PRESCRIPTION ─────────────────────────
# Schéma pour le corps du POST /prescriptions
# Permet de prescrire un médicament pour une consultation
# (ajoute une ligne dans la table pivot consultation_medicament)
# =====================================================

## PrescriptionCreate — corps de la requête POST /prescriptions
class PrescriptionCreate(BaseModel):
    consultation_id: int  # ID de la consultation qui reçoit la prescription — obligatoire
    medicament_id:   int  # ID du médicament prescrit — obligatoire

    