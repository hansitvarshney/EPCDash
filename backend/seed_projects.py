from backend.database import SessionLocal, Project

def seed_active_sites():
    db = SessionLocal()
    try:
        # Check if we already initialized projects to avoid duplication
        existing_count = db.query(Project).count()
        #if existing_count > 0:
           # print(f"ℹ️ Database already contains {existing_count} configured sites. Skipping seed.")
          #  return

        # Define real-world project profiles matching your dad's scale
        active_projects = [
            Project(id=1, name="Sector 65 Commercial High-Rise Complex"),
            Project(id=2, name="DLF Phase 5 Infrastructure Development"),
            Project(id=3, name="Sohna Road Turnkey Industrial Warehouse"),
        ]

        db.add_all(active_projects)
        db.commit()
        print("🚀 Successfully seeded enterprise project sites into the database!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding projects: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_active_sites()