# =====================================================
# main.py — Point d'entrée principal de l'application FastAPI
# Ce fichier définit tous les endpoints (routes) de l'API clinique
# Il utilise SQLAlchemy pour la base de données et Pydantic
# pour valider les données avant qu'elles n'entrent dans le système
# =====================================================

### ─── IMPORTATIONS PRINCIPALES ──────────────────────────────────────
# permet d'utiliser FastAPI, gérer les erreurs HTTP et faire l'injection de dépendances
from fastapi import FastAPI, Depends, HTTPException
# permet d'ouvrir une session pour communiquer avec la base de données
from sqlalchemy.orm import Session
# importe le moteur et la fonction de session définis dans database.py
from database import engine, get_db
# importe les modèles SQLAlchemy et les schémas Pydantic
import models, schemas

### ─── INITIALISATION DE L'APPLICATION ────────────────────────────────
# crée l'application FastAPI avec un titre affiché dans Swagger UI
app = FastAPI(title="API Clinique Medicale")

# crée toutes les tables dans la base de données automatiquement si elles n'existent pas encore
# SQLAlchemy lit les modèles et génère les instructions SQL CREATE TABLE correspondantes
models.Base.metadata.create_all(bind=engine)


# =====================================================
### ─── SECTION MÉDECIN ─────────────────────────────
# Endpoints pour gérer les médecins (CRUD complet)
# Relation : Medecin → Consultation (One-to-Many)
# =====================================================

## GET /medecins — retourne la liste de tous les médecins dans la base de données
@app.get("/medecins", response_model=list[schemas.MedecinOut])
def get_medecins(db: Session = Depends(get_db)):  # Depends(get_db) = FastAPI injecte la session automatiquement
    medecins = db.query(models.Medecin).all()  # récupère toutes les lignes de la table "medecins"
    return medecins  # FastAPI les convertit automatiquement en MedecinOut (Pydantic)



## GET /medecins/{id}/consultations — retourne la liste des consultations d'un médecin spécifique
# Rôle : vérifie que le médecin existe, puis retourne ses consultations (relation One-to-Many)
@app.get("/medecins/{id}/consultations", response_model=list[schemas.ConsultOut])
def get_consultations_medecin(id: int, db: Session = Depends(get_db)):
    medecin = db.query(models.Medecin).filter(models.Medecin.id == id).first()  # cherche le médecin par son ID
    if not medecin:
        raise HTTPException(status_code=404, detail="Medecin non trouve")  # 404 = le médecin n'existe pas en base
    return medecin.consultations  # retourne la liste des consultations via la relation SQLAlchemy (One-to-Many)


## POST /medecins — crée un nouveau médecin dans la base de données
# Pydantic valide le corps de la requête (MedecinCreate) avant que le code s'exécute
@app.post("/medecins", response_model=schemas.MedecinOut)
def create_medecin(medecin: schemas.MedecinCreate, db: Session = Depends(get_db)):
    nouveau = models.Medecin(          # crée un nouvel objet Medecin SQLAlchemy
        nom        = medecin.nom,      # prend la valeur du corps de requête Pydantic
        prenom     = medecin.prenom,   # permet d'assurer que chaque colonne reçoit la bonne donnée
        specialite = medecin.specialite
    )
    db.add(nouveau)      # ajoute le nouveau médecin à la session (pas encore en base de données)
    db.commit()          # sauvegarde les changements de manière permanente dans SQLite
    db.refresh(nouveau)  # rafraîchit l'objet pour récupérer l'ID généré par la base de données
    return nouveau       # retourne le médecin créé avec son ID (MedecinOut)



## DELETE /medecins/{id} — supprime un médecin par son ID
# Gestion d'erreur : 404 si le médecin n'est pas trouvé
@app.delete("/medecins/{id}")
def delete_medecin(id: int, db: Session = Depends(get_db)):
    medecin = db.query(models.Medecin).filter(models.Medecin.id == id).first()  # cherche le médecin par ID
    if not medecin:
        raise HTTPException(status_code=404, detail="Medecin non trouve")  # évite de supprimer un médecin inexistant
    db.delete(medecin)  # marque le médecin pour suppression dans la session
    db.commit()         # applique la suppression définitivement dans la base de données
    return {"message": f"Medecin {id} supprime avec succes"}  # confirme la suppression


## PUT /medecins/{id} — modifie les informations d'un médecin existant
# Pydantic valide les nouvelles données (MedecinCreate), gestion 404 si médecin absent
@app.put("/medecins/{id}", response_model=schemas.MedecinOut)
def update_medecin(id: int, medecin: schemas.MedecinCreate, db: Session = Depends(get_db)):
    db_medecin = db.query(models.Medecin).filter(models.Medecin.id == id).first()  # trouve le médecin existant
    if not db_medecin:
        raise HTTPException(status_code=404, detail="Medecin non trouve")  # 404 = médecin introuvable pour la mise à jour
    db_medecin.nom        = medecin.nom        # met à jour le nom avec la nouvelle valeur Pydantic
    db_medecin.prenom     = medecin.prenom     # met à jour le prénom
    db_medecin.specialite = medecin.specialite # met à jour la spécialité
    db.commit()            # sauvegarde les changements en base de données
    db.refresh(db_medecin) # rafraîchit l'objet pour refléter les données sauvegardées
    return db_medecin      # retourne le médecin mis à jour


# =====================================================
### ─── SECTION PATIENT ──────────────────────────────
# Endpoints pour gérer les patients (CRUD + relations)
# Relation : Patient → DossierMedical (One-to-One)
#            Patient → Consultation   (One-to-Many)
# =====================================================

    #pasyan
## GET /patients — retourne la liste de tous les patients dans la base de données
@app.get("/patients", response_model=list[schemas.PatientOut])
def get_patients(db: Session = Depends(get_db)):
    patients = db.query(models.Patient).all()  # récupère tous les patients de la table "patients"
    return patients  # PatientOut inclut le dossier (One-to-One) et les consultations (One-to-Many)


## GET /patients/{id} — retourne un seul patient par ID, AVEC son dossier médical (One-to-One)
# Rôle : afficher des données imbriquées — patient + dossier en une seule réponse
@app.get("/patients/{id}", response_model=schemas.PatientOut)
def get_patient(id: int, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == id).first()  # filtre par ID unique
    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouve")  # 404 = aucun patient avec cet ID
    return patient  # PatientOut inclut automatiquement le dossier et les consultations via les relations SQLAlchemy


## GET /patients/{id}/consultations — retourne la liste des consultations d'un patient spécifique
# Permet de voir l'historique médical d'un patient (relation One-to-Many)
@app.get("/patients/{id}/consultations", response_model=list[schemas.ConsultOut])
def get_consultations_patient(id: int, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == id).first()  # trouve le patient par ID
    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouve")  # 404 = le patient n'existe pas
    return patient.consultations  # retourne la liste des consultations via la relation One-to-Many SQLAlchemy


    #post pasyan yoooooooooooooooo
## POST /patients — crée un nouveau patient dans la base de données
# Pydantic (PatientCreate) valide : nom, prenom, date_naissance obligatoires
@app.post("/patients", response_model=schemas.PatientOut)
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    nouveau = models.Patient(                    # crée un objet Patient SQLAlchemy
        nom            = patient.nom,            # utilise les données validées par Pydantic
        prenom         = patient.prenom,         # garantit que les données sont correctes
        date_naissance = patient.date_naissance  # format "YYYY-MM-DD" — Pydantic vérifie que c'est une str
    )
    db.add(nouveau)      # ajoute le patient à la session
    db.commit()          # sauvegarde définitivement dans SQLite
    db.refresh(nouveau)  # rafraîchit pour obtenir l'ID généré automatiquement
    return nouveau       # retourne le patient créé (PatientOut)


    #put pasyan
## PUT /patients/{id} — modifie les informations d'un patient existant
@app.put("/patients/{id}", response_model=schemas.PatientOut)
def update_patient(id: int, patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    db_patient = db.query(models.Patient).filter(models.Patient.id == id).first()  # trouve le patient existant
    if not db_patient:
        raise HTTPException(status_code=404, detail="Patient non trouve")  # 404 = aucun patient à mettre à jour
    db_patient.nom            = patient.nom            # met à jour le nom
    db_patient.prenom         = patient.prenom         # met à jour le prénom
    db_patient.date_naissance = patient.date_naissance # met à jour la date de naissance
    db.commit()             # applique les changements en base de données
    db.refresh(db_patient)  # rafraîchit l'objet pour refléter les nouvelles données
    return db_patient       # retourne le patient mis à jour



#delete pasyan
## DELETE /patients/{id} — supprime un patient par son ID
@app.delete("/patients/{id}")
def delete_patient(id: int, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == id).first()  # cherche le patient
    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouve")  # évite de supprimer un patient inexistant
    db.delete(patient)  # marque le patient pour suppression
    db.commit()         # confirme la suppression en base de données
    return {"message": f"Patient {id} supprime avec succes"}  # retourne un message de confirmation


# =====================================================
### ─── SECTION DOSSIER MÉDICAL ─────────────────────
# Endpoints pour gérer les dossiers médicaux des patients
# Relation : Patient ↔ DossierMedical (One-to-One)
# Un seul patient = un seul dossier — garanti par unique=True
# =====================================================

#post dossier
## POST /dossiers — crée un dossier médical pour un patient
# Logique : 2 vérifications avant la création — le patient existe ? le dossier existe déjà ?
@app.post("/dossiers", response_model=schemas.DossierOut)
def create_dossier(dossier: schemas.DossierCreate, db: Session = Depends(get_db)):

    # Verifye 1 → patient egziste?
    # garantit qu'on ne crée pas un dossier "orphelin" sans patient
    patient = db.query(models.Patient).filter(
        models.Patient.id == dossier.patient_id
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouve")  # 404 = le patient n'existe pas en base

    # Verifye 2 → dossier deja egziste? (One-to-One!)
    # évite de violer la relation One-to-One — chaque patient = 1 seul dossier
    if patient.dossier:
        raise HTTPException(status_code=400, detail="Patient deja gen yon dossier")  # 400 = requête invalide (dossier déjà existant)

    # Kreye dossier
    # sauvegarde 4 colonnes : groupe sanguin, antécédents, allergies, et l'ID du patient
    nouveau = models.DossierMedical(
        groupe_sanguin = dossier.groupe_sanguin,  # ex : "A+", "O-", "AB+"
        antecedents    = dossier.antecedents,     # peut être vide (Optional dans Pydantic)
        allergies      = dossier.allergies,       # peut être vide aussi (Optional)
        patient_id     = dossier.patient_id       # clé étrangère qui lie le dossier au patient
    )
    db.add(nouveau)      # ajoute le dossier à la session
    db.commit()          # sauvegarde définitivement dans SQLite
    db.refresh(nouveau)  # rafraîchit pour obtenir l'ID du nouveau dossier
    return nouveau       # retourne le dossier créé (DossierOut)


## PUT /dossiers/{patient_id} — met à jour le dossier médical d'un patient par son ID
# Rôle : modifier le groupe sanguin, les antécédents ou les allergies d'un patient existant
@app.put("/dossiers/{patient_id}", response_model=schemas.DossierOut)
def update_dossier(patient_id: int, dossier: schemas.DossierBase, db: Session = Depends(get_db)):

    # Verifye patient egziste
    # évite de modifier le dossier d'un patient absent du système
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouve")  # 404 = patient introuvable

    # Verifye dossier egziste
    # évite une erreur Python si patient.dossier = None (relation vide)
    if not patient.dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouve pou patient sa")  # 404 = dossier pas encore créé

    # Mete ajou
    # SQLAlchemy trace les changements automatiquement — pas besoin de db.add()
    patient.dossier.groupe_sanguin = dossier.groupe_sanguin  # écrit le nouveau groupe sanguin
    patient.dossier.antecedents    = dossier.antecedents     # écrit les nouveaux antécédents
    patient.dossier.allergies      = dossier.allergies       # écrit les nouvelles allergies
    db.commit()                    # sauvegarde les changements en base de données
    db.refresh(patient.dossier)    # rafraîchit le dossier pour refléter les données mises à jour
    return patient.dossier         # retourne le dossier mis à jour (DossierOut)


# =====================================================
### ─── SECTION CONSULTATION ────────────────────────
# Endpoints pour gérer les consultations
# Relation : Medecin → Consultation (One-to-Many)
#            Patient → Consultation (One-to-Many)
#            Consultation ↔ Medicament (Many-to-Many)
# =====================================================

# CONSULTATIONS
## GET /consultations — retourne la liste de toutes les consultations dans la base de données
@app.get("/consultations", response_model=list[schemas.ConsultOut])
def get_consultations(db: Session = Depends(get_db)):
    consultations = db.query(models.Consultation).all()  # récupère toutes les consultations
    return consultations  # chaque ConsultOut inclut la liste des médicaments prescrits (Many-to-Many)




## GET /consultations/{id} — retourne une seule consultation AVEC ses médicaments prescrits
# Rôle : afficher des données imbriquées — consultation + médicaments (Many-to-Many) en une réponse
@app.get("/consultations/{id}", response_model=schemas.ConsultOut)
def get_consultation(id: int, db: Session = Depends(get_db)):
    consultation = db.query(models.Consultation).filter(
        models.Consultation.id == id  # filtre par ID unique de la consultation
    ).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation non trouve")  # 404 = consultation inexistante
    return consultation  # SQLAlchemy charge les médicaments automatiquement via la relation Many-to-Many


#post consultation
## POST /consultations — crée une nouvelle consultation
# Logique : vérifie que le patient ET le médecin existent avant de créer
@app.post("/consultations", response_model=schemas.ConsultOut)
def create_consultation(consult: schemas.ConsultCreate, db: Session = Depends(get_db)):

    # Verifye patient egziste
    # garantit que la consultation est associée à un patient valide
    patient = db.query(models.Patient).filter(
        models.Patient.id == consult.patient_id  # cherche le patient par l'ID fourni dans le corps de la requête
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouve")  # 404 = impossible de créer une consultation sans patient

    # Verifye medecin egziste
    # garantit que la consultation est associée à un médecin valide
    medecin = db.query(models.Medecin).filter(
        models.Medecin.id == consult.medecin_id  # cherche le médecin par l'ID fourni dans le corps de la requête
    ).first()
    if not medecin:
        raise HTTPException(status_code=404, detail="Medecin non trouve")  # 404 = impossible de créer une consultation sans médecin

    # Kreye consultation
    # sauvegarde 5 champs : date, motif, diagnostic, ID patient, ID médecin
    nouveau = models.Consultation(
        date       = consult.date,       # date de la consultation (format "YYYY-MM-DD")
        motif      = consult.motif,      # raison de la visite — obligatoire (vérifié par Pydantic)
        diagnostic = consult.diagnostic, # diagnostic du médecin — Optional (peut être vide)
        patient_id = consult.patient_id, # clé étrangère vers le patient — One-to-Many
        medecin_id = consult.medecin_id  # clé étrangère vers le médecin — One-to-Many
    )
    db.add(nouveau)      # ajoute la consultation à la session
    db.commit()          # sauvegarde définitivement en base de données
    db.refresh(nouveau)  # rafraîchit pour obtenir l'ID et les données complètes (médicaments = [] au départ)
    return nouveau       # retourne la consultation créée (ConsultOut)



## DELETE /consultations/{id} — supprime une consultation par son ID
# SQLAlchemy supprime automatiquement les lignes liées dans la table pivot consultation_medicament
@app.delete("/consultations/{id}")
def delete_consultation(id: int, db: Session = Depends(get_db)):
    consultation = db.query(models.Consultation).filter(
        models.Consultation.id == id  # trouve la consultation par ID
    ).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation non trouve")  # 404 = consultation introuvable
    db.delete(consultation)  # supprime la consultation (les lignes de la table pivot sont aussi supprimées)
    db.commit()              # confirme la suppression en base de données
    return {"message": f"Consultation {id} supprime avec succes"}  # retourne une confirmation


    #medicament ak konsiltasyon denye blok kod  poum fucking fin  ak main la loooooolll
    python# ═══════════════════════════════════
# MEDICAMENTS
# ═══════════════════════════════════

# =====================================================
### ─── SECTION MÉDICAMENTS ─────────────────────────
# Endpoints pour gérer le catalogue des médicaments
# Un médicament peut être prescrit dans plusieurs consultations
# (côté Many-to-Many via la table pivot consultation_medicament)
# =====================================================

## GET /medicaments — retourne la liste de tous les médicaments disponibles dans le système
@app.get("/medicaments", response_model=list[schemas.MedicamentOut])
def get_medicaments(db: Session = Depends(get_db)):
    medicaments = db.query(models.Medicament).all()  # récupère tous les médicaments de la table "medicaments"
    return medicaments  # retourne la liste des médicaments (MedicamentOut : id, nom, dosage)

## POST /medicaments — ajoute un nouveau médicament au catalogue
# Pydantic (MedicamentCreate) vérifie : nom et dosage obligatoires
@app.post("/medicaments", response_model=schemas.MedicamentOut)  # Nou mete MedicamentOut pou API a ka retounen id a, paske MedicamentCreate pa gen id.
def create_medicament(medicament: schemas.MedicamentCreate, db: Session = Depends(get_db)):
    nouveau = models.Medicament(
        nom    = medicament.nom,   # nom du médicament (ex : "Amoxicillin")
        dosage = medicament.dosage # dosage (ex : "500mg 3x par jour")
    )
    db.add(nouveau)      # ajoute le médicament à la session
    db.commit()          # sauvegarde définitivement en base de données
    db.refresh(nouveau)  # rafraîchit pour obtenir l'ID généré automatiquement
    return nouveau       # retourne le médicament créé (MedicamentOut)

# ═══════════════════════════════════
# PRESCRIPTIONS
# ═══════════════════════════════════

# =====================================================
### ─── SECTION PRESCRIPTION ─────────────────────────
# Endpoints pour gérer les prescriptions — lien Many-to-Many
# entre Consultation et Medicament via la table pivot
# SQLAlchemy gère la table pivot automatiquement (pas besoin de SQL direct)
# =====================================================

## POST /prescriptions — prescrit un médicament pour une consultation (Many-to-Many)
# Rôle : ajoute un médicament dans la liste des médicaments d'une consultation (via relation secondaire)
# Gestion d'erreurs : 404 si consultation/médicament introuvable, 400 si déjà prescrit
@app.post("/prescriptions", response_model=schemas.ConsultOut)
def create_prescription(prescription: schemas.PrescriptionCreate, db: Session = Depends(get_db)):
    consultation = db.query(models.Consultation).filter(
        models.Consultation.id == prescription.consultation_id  # trouve la consultation par ID
    ).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation non trouve")  # 404 = consultation inexistante

    medicament = db.query(models.Medicament).filter(
        models.Medicament.id == prescription.medicament_id  # trouve le médicament par ID
    ).first()
    if not medicament:
        raise HTTPException(status_code=404, detail="Medicament non trouve")  # 404 = médicament inexistant

    if medicament in consultation.medicaments:
        raise HTTPException(status_code=400, detail="Medicament deja preskri nan consultation sa")  # 400 = impossible de prescrire deux fois le même médicament

    consultation.medicaments.append(medicament)  # ajoute le médicament via la relation Many-to-Many (SQLAlchemy écrit dans la table pivot)
    db.commit()               # sauvegarde la nouvelle ligne dans consultation_medicament
    db.refresh(consultation)  # rafraîchit la consultation pour inclure le nouveau médicament
    return consultation       # retourne la consultation AVEC la liste des médicaments mise à jour (ConsultOut)

## DELETE /prescriptions/{cid}/{mid} — retire un médicament d'une consultation (Many-to-Many)
# cid = consultation_id, mid = medicament_id
# Rôle : supprime la ligne correspondante dans la table pivot consultation_medicament
@app.delete("/prescriptions/{cid}/{mid}", response_model=schemas.ConsultOut)
def delete_prescription(cid: int, mid: int, db: Session = Depends(get_db)):
    consultation = db.query(models.Consultation).filter(
        models.Consultation.id == cid  # trouve la consultation par son ID (cid)
    ).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation non trouve")  # 404 = consultation inexistante

    medicament = db.query(models.Medicament).filter(
        models.Medicament.id == mid  # trouve le médicament par son ID (mid)
    ).first()
    if not medicament:
        raise HTTPException(status_code=404, detail="Medicament non trouve")  # 404 = médicament absent du catalogue

    if medicament not in consultation.medicaments:
        raise HTTPException(status_code=404, detail="Medicament pa preskri nan consultation sa")  # 404 = médicament non prescrit, impossible de le retirer

    consultation.medicaments.remove(medicament)  # retire le médicament de la liste (SQLAlchemy supprime la ligne dans la table pivot)
    db.commit()               # sauvegarde — supprime la ligne dans consultation_medicament
    db.refresh(consultation)  # rafraîchit la consultation pour refléter la liste mise à jour
    return consultation       # retourne la consultation AVEC la liste des médicaments restants (ConsultOut)
