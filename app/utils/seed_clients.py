import argparse
import csv
from dataclasses import dataclass
from decimal import Decimal
from io import StringIO

from sqlalchemy import String, cast, select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.client import BalanceType, Client
from app.models.user import User


CLIENTS_CSV = """Company Name,Address L1,Address L2,GSTIN
KAPOOR FORGE,"B.P.T PLOT NO 268/280, KOLSA BUNDER,DARUKHANA","MAZGAON, MUMBAI - 400 010",27CLOPM0536L1ZO
KAPOOR FORGE,"GALA no 2, HILL TOP INDUSTRIAL ESTATE, SN NO 126, BELKADI,","VILLAGE - KAMAN, TAL - VASAI, DIS - PALGHAR 401208.",27CLOPM0536L1ZO
M A ENTERPRISES,"23, COAL DEPOT, HUTMENTS, FORSBERRY ROAD,","SWEREE, MUMBAI - 400 033.",27ACBPL7447F1ZK
M S FORGING WORKS,"FIRST FLOOR, KULSUM MANZIL, NAVA NAGAR, DOCKYARD ROAD,","MAZGAON, MUMBAI - 400 010.",27AABPK7966L1Z4
SUPER FORGE,"INDRA NAGAR, PLOT L4, FORSEBERRY ROAD,","SEWRI (E), MUMBAI - 400 033.",27ANKPC1194N1ZO
JYOTI OIL CORPORATION,"Sitafal Wadi 9 B, Mazgaon","MUMBAI - 400 010.",27AAAFJ0766C1ZQ
SAMAY SALES,"5288/190, SANMATI BUILDING,PANT NAGAR,","GHATKOPAR(E), MUMBAI - 400 075.",27APCPS7668R1ZP
MAHAVIR OIL CORPORATION,"503, PRABHAT APARTMENT SBD MARG","MAZGAON, MUMBAI - 400 010.",27AAGFM4684C1Z8
ASIAN PETRO TRADING CO,"4B/704 DHIRAJ ENCLAVE, W E HIGHWAY,","BORIVALI(E) MUMBAI - 400066.",27ANSPK4838M1Z5
SHREE BALAJI ENTERPRISES,"6/1st FLOOR, VENUAAI ARCADE, KOPAR C ROAD,","OPP JAIN TEMPLE, DOMBIVLI - 421202.",27BPQPS6443M1ZX
SHREEJI SALES CORPORATION,"HIGHLAND PARK, C-204 DHANUKAWADI LINKING ROAD","KANDIWALI (W) MUMBAI - 400067",27AFIPM5131R1ZW
AJUDIYA ENTERPRISES,"9, KAILASHDHAM SOCIETY, NEAR GAJERA SCHOOL,","KATARGAM, SURAT, GUJARAT-395004.",24AEEPA4523L1ZU
SUN ELECTRICAL INDUSTRIES,"1ST,FLOOR 1, HAPPY HOME, 50 TILAK NAGAR 90FT ROAD SAKINAKA","MUMBAI-400072",27AJRPA2196H1Z0
MEGHALAYA LUBRICANTS PRIVATE LIMITED,"44 FEET ROAD, KILLA NO 183 5/1/4,6/1/3, KHEWAT NO.718/634,","KHATA NO. 765, BAHADURGARH, Rohad, Jhajjar,Haryana, 124501",06AAGCM4017Q1Z6
ETERNAL OFFSHORE SERVICES PVT LTD,"OFFICE NO 211, PLOT NO 28, THE GREAT EASTERN CHEMBUR PREMISES","CO OPRATIVE SOCIETY SEC 11,BELABUR, NAVI MUMBAI 400614",27AAFCE4974M1Z1
DELUXE ENTERPRISES,"GILBERT COMPOUND SHOP NO 11, IMAM AHMED RAZA MARG,","KHAIRANI ROAD,ANDHERI EAST - 400072",27KCEPK8456G1Z3
SHUKLA TRADING COMPANY,"Unit No. M-3, Swastik Ind Estate, Goddev Phatak Road,","Bhayandar East, Thane, Maharashtra, 401105",27AINPS2688D1ZR
SHREE GANESH TRADING CO.,"R.M MEHTA COMPOUND NEAR B.P.T TOOL","SHRI GANESH TRADING COMPANY WADALA MUMBAI 400037",27AAAPT2434R1Z7
P S SUMUKHA PVT LTD,"SHOP NO. SB-175, 2ND FLOOR, HIGH LAND CORPORATE CENTER,","KAPURBAVADI JUNCTION, THANE (WEST) MAHARASTRA-27",27AALCP2819C1ZH
NISAT ENTERPRISES,"111-A MORLAND ROAD, JUMA MASJID BUILLDING","MUMBAI-400008",27AABPS9497C1Z9
A. B. ENTERPRISES,"ROOM NO 9, VIJAY TIWARI CHAWL, LOKMANYA TILAK NAGAR,","SAKINAKA, KURLA (W), MUMBAI-400072",27AYIPM3879M1ZK
REGAL TRADING COMPANY,"MILAN MARKIT PLOT NO 22, OPP DAIGHAR POLICE STATION BEHIND","KASHINATHWAJAN KATA MUMBRA PANVEL ROAD KALYAN PHATA THANE",27AMWPK0066G1ZS
S K OIL CORPORATION,"SHOP NO 1/A PLOT NO 1816 COAL DEPOT","FOSBERY ROAD SWREE MUMBAI -400015",27CWDPK7863C1ZE
CHAND GLOBAL FUEL,,"NARGAON KALYAN DIS THANE",27AAFCC7660Q1ZY
AL-SABA ENTERPRISES,"FLOOR GROUND, EAST INDIA COMPOUND, GALA NO.19, SETH WADI CHAWL","DHZRZVI, MAIN ROAD, DHARAVI MUMBAI, 400017",27ANLPS8338R1ZR
ABHISHEK LUBRICATION,"PRIVATE NIWAS, R. NO.7, ROSHAN NAGAR CHANDAVARKAR LANE,","BORIVALI-WEST, MUMBAI-401105",27AURPS6252P1ZI
MANHA TRADER,"GROUND, H NO 2338 GALA NO 3, NR SHUKRIYA HOTEL, NR ASMATI MASJID","NAGAON, BHIWANDI, THANE - 421302",27GCTPK0529K1Z1
CORPOIL TRADING,"FLOOR GROUND, EAST INDIA COMPOUND, GALA NO.19, SETH WASI CHAWL","RTO OFFICE ROAD NIRA ROAD E MIRA BHAYNDRA THANE",27AASFC7319N1ZP
ADORN OIL COMPANY,"PARVATI NIWAS, R.NO.7, ROSHAN NAGAR CHANDAVARKAR LANE,","CROSSING DHARAVI MAHIM EAST MUMBAI 400017",27CQYPK5210L1Z9
R J OIL CORPORATION,"103 PRABHAT APARTMENT 2ND GUN POWDER LANE","GHATKOPAR WEST MUMBAI-400086",27AXMPB7540D1ZM
VARMA INDUSTRIES,"COAL DEOT GROUND FLOOR HUTMENTS","FOSBERY ROAD SWREE MUMBAI -400015",27AHWPV5378D1ZH
NAJMI ENGINEERING WORKS,"PLOT NO2, SANAULLAH COMPOUND SION MAHIM LINK ROAD NEAR RAILWAY","MAZANINE STREET DARUKHANA MUMBAI - 400010",27AEEPD9737P1ZV
SHAH OIL CORPORATION,KANDIVALI WEST M-67,,27AHTPD5140N1ZX
TEJ ENTERPRISES,"behind patel xerox, 1702 building no 148, Rosell mayuresh,chs, Vallabh Bhag Lane pant nagar","Ghatkopar East,Mumbai, Mumbai Suburban, Maharashtra, 400075",27APCPS7669Q1ZQ
ARHAM LUBRICANT AND COMPANY,"Ground Floor Shop No. 20 Rapid Jewid Old Mumbai Pune Highway Khalapur","Hal kh Raigad Maharastra 410202",27AGJPO5909K1ZV
YASH PETRO CHEM,"A WING, BUILLDING NO.107, 10TH FLOOR FLAT NO.1002, TILAK NAGAR","CHEMBUR,MUMBAI-400089",27ACRPS7957H1ZM
SANTOSH OIL DEPOT,"PLOT NO.167, GALA NO. A-1/A-2, GAYADIN HOUSE, GOGTEWADI,","OFF.AREY ROAD, GOREGAON EAST, Mumbai - 400063",27ACYPC9176D1Z4
FAMOUS RUBO MOULD INDUSTRIES,REHNAN KHAN COMPOUND BYCULLA EAST MUMBAI,,27AAZPS3057L1ZQ
SUN ELECTRICAL INDUSTRIES,"1ST,FLOOR 1, HAPPY HOME, 50 TILAK NAGAR 90FT ROAD SAKINAKA","MUMBAI-400072",27AJRPA2196H1Z0
BHARAT CHEMICAL INDUSTRIES,"9/B, SITAFAL WADI, 3rd LANE,","MAZGAON, MUMBAI - 400 010.",27AAAFB0914E1Z4
SWASTIK TRADERS,"103, PRABHAT APARTMENT 2ND GUN POWDER LANE","MAZGAON MUMBAI 400010",27AHZPS4710R1Z6
FAMOUS RUBO MOULD INDUSTRIES,REHNAN KHAN COMPOUND BYCULLA EAST MUMBAI,,27AAZPS3057L1ZQ
MEGHALAYA LUBRICANTS PRIVATE LIMITED,"44 FEET ROAD, KILLA NO 183 5/1/4,6/1/3, KHEWAT NO.718/634,","KHATA NO. 765, BAHADURGARH, Rohad, Jhajjar,Haryana, 124501",06AAGCM4017Q1Z6
TEJ ENTERPRISES,"behind patel xerox, 1702 building no 148, Rosell mayuresh,chs, Vallabh Bhag Lane pant nagar","Ghatkopar East,Mumbai, Mumbai Suburban, Maharashtra, 400075",27APCPS7669Q1ZQ
I. K. TRADERS,"Bhartiya Kamla Nagar, Shaikh Misree Road,Sangam Nagar,","Antop Hill Wadala, MUMBAI - 400037.",27NNUPS3813P1ZN
ARIHANT ENTERPRISES,"4TH FLOOR ROOM NO.17, TILAK ROAD TAI PINGAL CHOWK","DOMBIVALI EAST KALYAN THANE MAHARASTRA-411201",27AMLPM0666P1ZC
AJUDIYA ENTERPRISES,DAIMAND NAGAR KAMREJ 342 NO,LASAKANA SURAT,24AEEPA4523L1ZU
Nayan enterprise,"2 / 604 s.n.trimurti chs ltd SIDHARTH NAGAR r.d no 16","Near joggas park Goregaon west Mumbai 400104",27AAFPS6825E1ZJ
SHREEJI SALES CORPORATION,"HIGHLAND PARK, C-204 DHANUKAWADI LINKING ROAD","KANDIWALI (W) MUMBAI - 400067",27AFIPM5131R1ZW
GAURAV ENTERPRISIES,"C/3 SHRI MAHAVIR PRASAD CHSL, SUBHASH NAGAR ESTATE","390 N M JOSHI MARG MUMBAI 400011",27AYHPS2710A1ZS
A G ASHTAVINAYAKA PETROCHEM PVT.LTD,"SURVEY NO-222, VILLAGE-HEDAVALI, TI-SUDHAGAD KHOPOLI","DIST-RAIGAD MAHARASHTRA-27",27AAKCA0034H1Z0
MIZAAN ENTERPRISES,"PLOT NO 222,TIN SHED, KOLSA BUNDER ROAD, GUPTA COMPOUND,","DARUKHANA, MAZGAON, MUMBAI - 400 010.",27AQYPA2012J1ZV
NISAT ENTERPRISES,"111-A, MORLAND ROAD, JUMA MASJID BUILDING","MUMBAI - 400008",27AABPS9497C1Z9
TORCO OILS PRIVATE LIMITED,"PHASE-I, 454, HSIIDC, INDUSTRIAL ESTATE, BARHI,","Sonipat, Haryana, 131001",06AAPCS6024C1ZH
GAYATRI SALES CORPORATION,"House No. 307, Gala No. 9, Khokha Compound Next to Duttatrey Compound","BehindYogesh Hotel, Bhiwandi 421302",27ACVPV7243F1ZW
LUBRIC OILS,"CW 636, NR. PETROL PUMP, SANJAY GANDHI TRANSPORT NAGAR,","North West Delhi, Delhi, 110042",07AJHPT8949H1ZG
BHARAT OIL AGENCY,"PLOT NO. P 14,","MIDC NAGAPUR, 414111",27AAIFB5681J1Z3
"""


@dataclass(frozen=True)
class ClientSeedRow:
    client_name: str
    address: str | None
    gstin: str


def _clean(value: str | None) -> str:
    return " ".join((value or "").replace("\r", " ").split())


def _normalize_gstin(value: str) -> str:
    return _clean(value).upper()


def _load_rows() -> list[ClientSeedRow]:
    rows: list[ClientSeedRow] = []
    reader = csv.DictReader(StringIO(CLIENTS_CSV))
    for raw in reader:
        name = _clean(raw["Company Name"])
        address_parts = [_clean(raw["Address L1"]), _clean(raw["Address L2"])]
        address = ", ".join(part for part in address_parts if part) or None
        gstin = _normalize_gstin(raw["GSTIN"])
        if not name or not gstin:
            continue
        rows.append(ClientSeedRow(client_name=name, address=address, gstin=gstin))
    return rows


def _resolve_created_by(db: Session, email: str | None) -> User:
    if email:
        user = db.scalar(select(User).where(User.email == email.lower()))
        if user is None:
            raise RuntimeError(f"No user found with email {email!r}.")
        return user

    user = db.scalar(
        select(User)
        .where(cast(User.role, String).in_(["superadmin", "admin"]))
        .order_by(User.id.asc())
        .limit(1)
    )
    if user is None:
        raise RuntimeError("Create a superadmin/admin first, or pass --created-by-email.")
    return user


def import_clients(db: Session, *, created_by_email: str | None = None, dry_run: bool = False) -> None:
    created_by = _resolve_created_by(db, created_by_email)
    seen_gstins: set[str] = set()
    inserted = 0
    updated = 0
    skipped_duplicates = 0
    skipped_invalid = 0

    for row in _load_rows():
        if len(row.gstin) != 15:
            skipped_invalid += 1
            print(f"Skipping invalid GSTIN {row.gstin!r} for {row.client_name}")
            continue

        if row.gstin in seen_gstins:
            skipped_duplicates += 1
            print(f"Skipping duplicate GSTIN in seed data: {row.gstin} ({row.client_name})")
            continue
        seen_gstins.add(row.gstin)

        existing = db.scalar(select(Client).where(Client.gstin == row.gstin))
        if existing:
            existing.client_name = row.client_name
            existing.billing_name = row.client_name
            existing.address = row.address
            updated += 1
            continue

        db.add(
            Client(
                client_name=row.client_name,
                billing_name=row.client_name,
                address=row.address,
                gstin=row.gstin,
                opening_balance=Decimal("0.00"),
                balance_type=BalanceType.debit,
                current_balance=Decimal("0.00"),
                created_by_user_id=created_by.id,
            )
        )
        inserted += 1

    if dry_run:
        db.rollback()
    else:
        db.commit()

    action = "Would import" if dry_run else "Imported"
    print(
        f"{action} clients: inserted={inserted}, updated={updated}, "
        f"duplicate_rows_skipped={skipped_duplicates}, invalid_rows_skipped={skipped_invalid}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Import seed client master data.")
    parser.add_argument("--created-by-email", help="Existing admin/superadmin email to own new clients.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print counts without saving.")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        import_clients(db, created_by_email=args.created_by_email, dry_run=args.dry_run)
    finally:
        db.close()


if __name__ == "__main__":
    main()
