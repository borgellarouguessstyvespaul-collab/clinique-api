# =====================================================
# models.py — Définit la structure des tables de la base de données (ORM)
# Chaque classe = une table dans la base de données SQLite
# =====================================================

# Importation des outils SQLAlchemy pour créer les colonnes et relations
from sqlalchemy import Column, Integer, String, Text, Table, ForeignKey
from sqlalchemy.orm import relationship

# Importation de Base définie dans database.py — tous les modèles doivent en hériter
from database import Base


# ----------------------------------------------------
# TABLE PIVOT — Many-to-Many : Consultation <-> Medicament
# Une consultation peut avoir plusieurs médicaments
# Un médicament peut apparaître dans plusieurs consultations
# C'est pourquoi nous utilisons une table intermédiaire (pivot)
# ----------------------------------------------------
consultation_medicament = Table(
    "consultation_medicament",      # nom de la table dans la base de données
    Base.metadata,                  # rattaché aux métadonnées de Base
    Column("consultation_id", Integer, ForeignKey("consultations.id"), primary_key=True),  # clé étrangère vers consultation
    Column("medicament_id",   Integer, ForeignKey("medicaments.id"),   primary_key=True)   # clé étrangère vers médicament
)


# ----------------------------------------------------
# MODÈLE Medecin — représente la table "medecins" en base de données
# Un médecin peut faire plusieurs consultations (One-to-Many)
# ----------------------------------------------------
class Medecin(Base):
    __tablename__ = "medecins"  # nom de la table dans SQLite

    # Clé primaire — SQLAlchemy la crée automatiquement (1, 2, 3…)
    id         = Column(Integer, primary_key=True, index=True)

    # Nom et prénom du médecin — obligatoire (nullable=False)
    nom        = Column(String(100), nullable=False)
    prenom     = Column(String(100), nullable=False)

    # Spécialité du médecin (exemple: Pédiatrie, Chirurgie…)
    specialite = Column(String(100), nullable=False)

    # Relation : un médecin peut avoir plusieurs consultations
    # back_populates connecte la relation avec la classe Consultation
    consultations = relationship("Consultation", back_populates="medecin")


# ----------------------------------------------------
# MODÈLE Patient — représente la table "patients" en base de données
# Un patient peut avoir 1 dossier médical et plusieurs consultations
# ----------------------------------------------------
class Patient(Base):
    __tablename__ = "patients"  # nom de la table dans SQLite

    # Clé primaire — ID unique pour chaque patient
    id             = Column(Integer, primary_key=True, index=True)

    # Nom et prénom du patient — obligatoire
    nom            = Column(String(100), nullable=False)
    prenom         = Column(String(100), nullable=False)

    # Date de naissance du patient (format texte : "YYYY-MM-DD")
    date_naissance = Column(String(20), nullable=False)

    # Relation One-to-One : 1 patient → 1 seul dossier médical
    # uselist=False indique à SQLAlchemy que ce n'est pas une liste, mais un seul objet
    dossier = relationship(
        "DossierMedical",
        back_populates="patient",
        uselist=False
    )

    # Relation One-to-Many : 1 patient → plusieurs consultations
    consultations = relationship("Consultation", back_populates="patient")


# ----------------------------------------------------
# MODÈLE DossierMedical — représente la table "dossiers_medicaux"
# Chaque patient a un seul dossier médical (One-to-One)
# ----------------------------------------------------
class DossierMedical(Base):
    __tablename__ = "dossiers_medicaux"  # nom de la table dans SQLite

    # Clé primaire — ID unique pour chaque dossier
    id             = Column(Integer, primary_key=True, index=True)

    # Groupe sanguin du patient (exemple : A+, O-, AB+…)
    groupe_sanguin = Column(String(5), nullable=False)

    # Antécédents médicaux — peut être vide (nullable=True)
    antecedents    = Column(Text, nullable=True)

    # Allergies du patient — peut être vide aussi
    allergies      = Column(Text, nullable=True)

    # Clé étrangère — lie le dossier à un seul patient
    # unique=True garantit que 2 dossiers ne peuvent pas appartenir au même patient
    patient_id = Column(Integer, ForeignKey("patients.id"), unique=True, nullable=False)

    # Relation inverse — retourne l'objet Patient qui possède le dossier
    patient = relationship("Patient", back_populates="dossier")


# ----------------------------------------------------
# MODÈLE Consultation — représente la table "consultations"
# Une consultation lie un patient et un médecin
# ----------------------------------------------------
class Consultation(Base):
    __tablename__ = "consultations"  # nom de la table dans SQLite

    # Clé primaire — ID unique pour chaque consultation
    id         = Column(Integer, primary_key=True, index=True)

    # Date de la consultation (format texte : "YYYY-MM-DD")
    date       = Column(String(20), nullable=False)

    # Motif de la visite (exemple: "Fièvre", "Douleur au ventre"…) — obligatoire
    motif      = Column(Text, nullable=False)

    # Diagnostic posé par le médecin — peut être vide au début
    diagnostic = Column(Text, nullable=True)

    # Clé étrangère vers le patient — quel patient est venu ?
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)

    # Clé étrangère vers le médecin — quel médecin l'a reçu ?
    medecin_id = Column(Integer, ForeignKey("medecins.id"), nullable=False)

    # Relation vers l'objet Patient (back_populates connecte les 2 côtés)
    patient = relationship("Patient", back_populates="consultations")

    # Relation vers l'objet Medecin
    medecin = relationship("Medecin", back_populates="consultations")

    # Relation Many-to-Many vers Medicament via la table pivot
    # secondary=consultation_medicament est la table intermédiaire
    medicaments = relationship(
        "Medicament",
        secondary=consultation_medicament,
        back_populates="consultations"
    )


# ----------------------------------------------------
# MODÈLE Medicament — représente la table "medicaments"
# Un médicament peut apparaître dans plusieurs consultations
# ----------------------------------------------------
class Medicament(Base):
    __tablename__ = "medicaments"  # nom de la table dans SQLite

    # Clé primaire — ID unique pour chaque médicament
    id     = Column(Integer, primary_key=True, index=True)

    # Nom du médicament (exemple : Amoxicillin, Paracetamol…)
    nom    = Column(String(100), nullable=False)

    # Dosage du médicament (exemple : "500mg", "2x par jour"…)
    dosage = Column(String(50), nullable=False)

    # Relation Many-to-Many inverse — quelles consultations utilisent ce médicament ?
    consultations = relationship(
        "Consultation",
        secondary=consultation_medicament,
        back_populates="medicaments"
    )