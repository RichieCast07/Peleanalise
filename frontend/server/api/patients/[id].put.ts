import { z } from "zod";
import { prisma } from "../../utils/prisma";
import { getAuthUser } from "../../utils/rbac";
import { auditLog } from "../../utils/audit";

// "" = campo vacío del formulario: se ignora.
const optional = <T extends z.ZodTypeAny>(s: T) =>
  z.preprocess((v) => (v === "" || v === null ? undefined : v), s.optional());

const schema = z.object({
  firstName:    optional(z.string().min(2).max(100)),
  lastName:     optional(z.string().min(2).max(100)),
  sex:          optional(z.enum(["MASCULINO", "FEMENINO", "OTRO"])),
  birthDate:    optional(z.string().regex(/^\d{4}-\d{2}-\d{2}$/)),
  curp:         optional(z.string().length(18, "La CURP debe tener 18 caracteres").toUpperCase()),
  phone:        optional(z.string().max(20)),
  email:        z.string().email().optional().or(z.literal("")),
  address:      optional(z.string().max(500)),
  observations: optional(z.string().max(2000)),
});

export default defineEventHandler(async (event) => {
  const auth   = getAuthUser(event);
  const id     = getRouterParam(event, "id")!;
  const body   = await readBody(event);
  const parsed = schema.safeParse(body);
  if (!parsed.success) {
    throw createError({ statusCode: 422, message: parsed.error.issues[0]?.message ?? "Datos inválidos" });
  }
  const data = parsed.data;

  const update: Record<string, unknown> = { ...data };
  if (data.birthDate) update.birthDate = new Date(data.birthDate);
  if (data.email === "") update.email = null;

  const patient = await prisma.patient.update({
    where: { id, deletedAt: null },
    data:  update,
  });

  await auditLog(event, "UPDATE", "patients", id, auth.userId);
  return patient;
});
