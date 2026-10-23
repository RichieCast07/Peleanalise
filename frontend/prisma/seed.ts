import { PrismaClient, RoleType } from "@prisma/client";
import bcrypt from "bcryptjs";

const prisma = new PrismaClient();

async function main() {
  // En un despliegue público define SEED_ADMIN_PASSWORD, SEED_DOCTOR_PASSWORD y SEED_CAPTURISTA_PASSWORD
  // para no dejar las contraseñas de ejemplo (Admin123!, etc.).
  const adminHash  = await bcrypt.hash(process.env.SEED_ADMIN_PASSWORD      ?? "Admin123!", 12);
  const doctorHash = await bcrypt.hash(process.env.SEED_DOCTOR_PASSWORD     ?? "Doctor123!", 12);
  const capHash    = await bcrypt.hash(process.env.SEED_CAPTURISTA_PASSWORD ?? "Capturista123!", 12);

  await prisma.user.upsert({
    where: { email: "admin@peleanalise.mx" },
    update: {},
    create: {
      email: "admin@peleanalise.mx",
      password: adminHash,
      firstName: "Super",
      lastName: "Administrador",
      role: RoleType.ADMIN,
    },
  });

  await prisma.user.upsert({
    where: { email: "doctor@peleanalise.mx" },
    update: {},
    create: {
      email: "doctor@peleanalise.mx",
      password: doctorHash,
      firstName: "Dra. María",
      lastName: "González López",
      role: RoleType.DOCTOR,
    },
  });

  await prisma.user.upsert({
    where: { email: "capturista@peleanalise.mx" },
    update: {},
    create: {
      email: "capturista@peleanalise.mx",
      password: capHash,
      firstName: "Carlos",
      lastName: "Ramírez Torres",
      role: RoleType.CAPTURISTA,
    },
  });

  console.log("✓ Seed completado");
}

main()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
