print("SCRIPT STARTED")

import asyncio
from database import AsyncSessionLocal
from models import Institution, Programme, CompetencyUnit, User, Placement, PlacementStatus, EvidenceSubmission, Assessment, UserRole
from security import hash_password
from datetime import datetime

async def seed():
    print("SEED FUNCTION STARTED")
    async with AsyncSessionLocal() as session:
        # Create an institution
        institution = Institution(name="The Kiambu National Polytechnic")
        session.add(institution)
        await session.commit()
        print(f"Institution created with ID: {institution.id}")
        

        # Create a programme
        programme = Programme(institution_id = institution.id ,name="Computer Science Level 6",)
        session.add(programme)
        await session.commit()

        # Create competency units
        competency_unit1 = CompetencyUnit(programme_id = programme.id, code = "CSC101", name = "Introduction to Programming")

        competency_unit2 = CompetencyUnit(programme_id = programme.id, code = "CSC102", name = "Data Structures and Algorithms")

        competency_unit3 = CompetencyUnit(programme_id = programme.id, code = "CSC103", name ="Networking and Distributed Systems")

        competency_unit4 = CompetencyUnit(programme_id = programme.id, code = "CSC104", name = "Database Management Skills")

        competency_unit5 = CompetencyUnit(programme_id = programme.id, code = "CSC105", name = "Develop an Information System")

        # Adding the competency units to the session
        session.add_all([competency_unit1, competency_unit2, competency_unit3, competency_unit4, competency_unit5])
        # Commit the changes to the database
        await session.commit()

        # Create a user
        user = User(institution_id = institution.id, email = "victor@kiambupoly.ac.ke", hashed_password = hash_password("victor123"), full_name = "Victor Wanjala", role = UserRole.SUPERVISOR)
        session.add(user)
        await session.commit()

        # TODO: Create 2 student Users, then Placement
        # Placement needs student.id and supervisor.id - commit users first

                # Create student users
        student1 = User(institution_id = institution.id, programme_id = programme.id, email = "aaron@kiambupoly.ac.ke", hashed_password = hash_password("aaron123"), full_name = "Aaron Minish", role = UserRole.STUDENT)
        session.add(student1)

        student2 = User(institution_id = institution.id, programme_id = programme.id, email = "lorrraine@kiambupoly.ac.ke", hashed_password = hash_password("lorraine123"), full_name = "Lorraine Sirengo", role = UserRole.STUDENT)
        session.add(student2)
        await session.commit()

        # Create placements for the students
        placement1 = Placement(student_id = student1.id, supervisor_id = user.id, status = PlacementStatus.ACTIVE, company_name = "Copy Cat Group",start_date = datetime(2026, 4, 12), end_date = datetime(2026, 8, 22))
        session.add(placement1)

        placement2 = Placement(student_id = student2.id, supervisor_id = user.id, status = PlacementStatus.PENDING, company_name = "Safaricom PLC", start_date = datetime(2026, 8, 17), end_date = datetime(2026, 11, 20))
        session.add(placement2)
        await session.commit()

        print("Seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed())