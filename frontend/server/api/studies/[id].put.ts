import { z } from "zod";
import { prisma } from "../../utils/prisma";
import { requireRoles, getAuthUser } from "../../utils/rbac";
import { auditLog } from "../../utils/audit";

const schema = z.object({
  lesionType:       z.enum(["MELANOMA","NEVUS","CARCINOMA_BASOCELULAR","CARCINOMA_ESPINOCELULAR","QUERATOSIS_ACTINCA","DERMATOFIBROMA","LESION_VASCULAR","OTRO"]).optional(),
  anatomicLocation: z.string().min(2, "La localización debe tener al menos 2 caracteres").max(200).optional(),
  // "" = campo vaciado en el formulario → se guarda como sin comentarios
  clinicalComments: z.string().max(2000, "Los comentarios no pueden pasar de 2000 caracteres").optional(),
  studyDate:        z.string().regex(/^\d{4}-\d{2}-\d{2}/, "Fecha inválida").optional(),
});

export default defineEventHandler(async (event) => {
  requireRoles(event, "ADMIN", "DOCTOR", "CAPTURISTA");
  const auth = getAuthUser(event);
  const id   = getRouterParam(event, "id")!;

  const parsed = schema.safeParse(await readBody(event));
  if (!parsed.success) {
    throw createError({ statusCode: 422, message: parsed.error.issues[0]?.message ?? "Datos inválidos" });
  }
  const data = parsed.data;

  const exists = await prisma.study.findFirst({ where: { id, deletedAt: null }, select: { id: true } });
  if (!exists) throw createError({ statusCode: 404, message: "Estudio no encontrado" });

  const study = await prisma.study.update({
    where: { id },
    data: {
      ...(data.lesionType       !== undefined && { lesionType: data.lesionType }),
      ...(data.anatomicLocation !== undefined && { anatomicLocation: data.anatomicLocation }),
      ...(data.clinicalComments !== undefined && { clinicalComments: data.clinicalComments.trim() || null }),
      ...(data.studyDate        !== undefined && { studyDate: new Date(data.studyDate) }),
    },
    include: { patient: { select: { id: true, firstName: true, lastName: true } } },
  });

  await auditLog(event, "UPDATE", "studies", id, auth.userId, { campos: Object.keys(data) });
  return study;
});
