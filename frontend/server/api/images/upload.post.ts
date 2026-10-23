import { prisma } from "../../utils/prisma";
import { getAuthUser } from "../../utils/rbac";
import { saveFile } from "../../utils/storage";
import { auditLog } from "../../utils/audit";

const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_SIZE_BYTES = 20 * 1024 * 1024;

export default defineEventHandler(async (event) => {
  const auth     = getAuthUser(event);
  const formData = await readMultipartFormData(event);

  if (!formData) throw createError({ statusCode: 400, message: "Sin datos de formulario" });

  const studyIdField = formData.find((f) => f.name === "studyId");
  const imageFile    = formData.find((f) => f.name === "image");

  if (!studyIdField?.data || !imageFile?.data) {
    throw createError({ statusCode: 400, message: "studyId e image son requeridos" });
  }

  const studyId  = studyIdField.data.toString();
  const mimeType = imageFile.type ?? "image/jpeg";
  const filename = imageFile.filename ?? "upload.jpg";

  if (!ALLOWED_TYPES.includes(mimeType)) {
    throw createError({ statusCode: 400, message: "Tipo de imagen no permitido (jpeg, png, webp)" });
  }

  if (imageFile.data.length > MAX_SIZE_BYTES) {
    throw createError({ statusCode: 400, message: "Imagen demasiado grande (máx. 20MB)" });
  }

  const study = await prisma.study.findFirst({ where: { id: studyId, deletedAt: null } });
  if (!study) throw createError({ statusCode: 404, message: "Estudio no encontrado" });

  let saved: Awaited<ReturnType<typeof saveFile>>;
  try {
    saved = await saveFile(Buffer.from(imageFile.data), filename, `studies/${studyId}`, mimeType);
  } catch (err) {
    console.error("[upload] no se pudo guardar la imagen:", err);
    const reason = err instanceof Error ? err.message : "error desconocido";
    throw createError({ statusCode: 502, message: `No se pudo guardar la imagen: ${reason}` });
  }
  const { publicUrl, filename: savedFilename } = saved;

  const image = await prisma.image.create({
    data: {
      studyId,
      type:        "ORIGINAL",
      filename:    savedFilename,
      storagePath: publicUrl,   // e.g. /uploads/studies/xxx/uuid.jpg
      mimeType,
      sizeBytes:   imageFile.data.length,
    },
  });

  await auditLog(event, "CREATE", "images", image.id, auth.userId, { studyId });
  return image;
});
