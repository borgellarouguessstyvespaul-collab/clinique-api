# =====================================================
# database.py — Configuration de la connexion à la base de données
# Ce fichier crée le moteur SQLAlchemy et la session de base de données
# =====================================================

# Importe create_engine pour créer la connexion avec la base de données
from sqlalchemy import create_engine

# declarative_base pour créer la classe Base — tous les modèles doivent en hériter
from sqlalchemy.ext.declarative import declarative_base

# sessionmaker pour créer des sessions — chaque session est une "conversation" avec la base
from sqlalchemy.orm import sessionmaker


# ----------------------------------------------------
# LIEN BASE DE DONNÉES — URL de connexion pour SQLite
# sqlite:///./clinique.db = crée le fichier "clinique.db"
# dans le même répertoire où nous exécutons l'application
# ----------------------------------------------------
DATABASE_URL = "sqlite:///./clinique.db"


# ----------------------------------------------------
# MOTEUR (ENGINE) — point d'entrée pour toute communication
# avec la base de données
# connect_args={"check_same_thread": False} — nécessaire
# pour que SQLite puisse travailler avec FastAPI (plusieurs fils/threads)
# ----------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)


# ----------------------------------------------------
# SESSION — objet que nous utilisons pour faire le CRUD (Create, Read,
# Update, Delete) dans la base de données
# autocommit=False → nous devons faire commit() manuellement
# autoflush=False  → n'envoie pas les changements automatiquement
# bind=engine      → connecte la session au moteur
# ----------------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ----------------------------------------------------
# BASE — classe parente que tous les modèles doivent hériter
# Chaque classe qui fait "class MonModele(Base)" créera
# une table automatiquement dans la base de données
# ----------------------------------------------------
Base = declarative_base()


# ----------------------------------------------------
# FONCTION get_db() — dépendance (dependency) FastAPI
# Crée une session pour chaque requête HTTP, puis la ferme
# après que la requête soit terminée (grâce au bloc finally)
# yield = FastAPI peut l'utiliser comme injection de dépendance
# ----------------------------------------------------
def get_db():
    db = SessionLocal()  # ouvre une nouvelle session
    try:
        yield db          # fournit la session à la route pour qu'elle travaille avec
    finally:
        db.close()        # ferme la session même s'il y a une erreur