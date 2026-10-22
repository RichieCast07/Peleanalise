import { prisma } from "../../utils/prisma";
import { requireRoles, getAuthUser } from "../../utils/rbac";
import { auditLog } from "../../utils/audit";

// Borrado lógico: el estudio deja de mostrarse pero se conserva en la base (trazabilidad clínica).
export default defineEventHandler(async (event) => {
  requireRoles(event, "ADMIN", "DOCTOR");
  const auth = getAuthUser(event);
  const id   = getRouterParam(event, "id")!;

  const study = await prisma.study.findFirst({ where: { id, deletedAt: null }, select: { id: true, patientId: true } });
  if (!study) throw createError({ statusCode: 404, message: "Estudio no encontrado" });

  await prisma.study.update({ where: { id }, data: { deletedAt: new Date() } });
  await auditLog(event, "DELETE", "studies", id, auth.userId, { patientId: study.patientId });
  return { message: "Estudio eliminado" };
});
