from backend.database import SessionLocal, Project

def force_reset_projects():
    db = SessionLocal()
    try:
        # Clear out existing project records to avoid conflicts
        print("🗑️ Clearing existing project entries...")
        db.query(Project).delete()
        
        # Define real-world project profiles matching your dad's scale
        active_projects = [
            Project(id=1, name="Sector 65 Commercial High-Rise Complex"),
            Project(id=2, name="DLF Phase 5 Infrastructure Development"),
            Project(id=3, name="Sohna Road Turnkey Industrial Warehouse"),
        ]

        db.add_all(active_projects)
        db.commit()
        print("🚀 Successfully forced seeded enterprise project sites into the database!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error resetting projects: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    force_reset_projects()