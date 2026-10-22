import { z } from "zod";
import { prisma } from "../../utils/prisma";
import { getAuthUser } from "../../utils/rbac";
import { auditLog } from "../../utils/audit";
import { handlePrismaError } from "../../utils/errors";

// El formulario envía "" en los campos que se dejan vacíos: se tratan como no enviados.
const optional = <T extends z.ZodTypeAny>(s: T) =>
  z.preprocess((v) => (v === "" || v === null ? undefined : v), s.optional());

const schema = z.object({
  firstName:    z.string().min(2).max(100),
  lastName:     z.string().min(2).max(100),
  sex:          z.enum(["MASCULINO", "FEMENINO", "OTRO"]),
  birthDate:    z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Formato: YYYY-MM-DD"),
  curp:         optional(z.string().length(18, "La CURP debe tener 18 caracteres").toUpperCase()),
  phone:        optional(z.string().max(20)),
  email:        z.string().email().optional().or(z.literal("")),
  address:      optional(z.string().max(500)),
  observations: optional(z.string().max(2000)),
});

export default defineEventHandler(async (event) => {
  const auth   = getAuthUser(event);
  const body   = await readBody(event);
  const parsed = schema.safeParse(body);
  if (!parsed.success) {
    throw createError({ statusCode: 422, message: parsed.error.issues[0]?.message ?? "Datos inválidos" });
  }
  const data = parsed.data;

  try {
    const patient = await prisma.patient.create({
      data: { ...data, birthDate: new Date(data.birthDate), email: data.email || null },
    });
    await auditLog(event, "CREATE", "patients", patient.id, auth.userId);
    return patient;
  } catch (err) {
    throw handlePrismaError(err);
  }
});
