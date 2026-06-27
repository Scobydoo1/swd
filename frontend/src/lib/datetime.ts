// Hiển thị thời gian theo giờ Việt Nam (Asia/Ho_Chi_Minh).
// Backend lưu mốc thời gian theo UTC nhưng serialize dạng naive ISO
// ("2026-06-27T10:30:00" - không có hậu tố Z). Trình duyệt sẽ hiểu nhầm
// chuỗi naive là giờ LOCAL -> lệch giờ. Vì vậy ta coi mọi mốc không có
// thông tin timezone là UTC, rồi format sang giờ VN.

const VN_TZ = "Asia/Ho_Chi_Minh";

/** Chuẩn hóa chuỗi ISO từ backend thành Date đúng (naive => UTC). */
export function parseServerDate(iso: string): Date {
  if (!iso) return new Date(NaN);
  // Đã có timezone (Z hoặc +hh:mm / -hh:mm sau phần giờ) thì dùng nguyên.
  const hasTz = /[zZ]$|[+-]\d{2}:?\d{2}$/.test(iso);
  return new Date(hasTz ? iso : iso + "Z");
}

const dateTimeFmt = new Intl.DateTimeFormat("vi-VN", {
  timeZone: VN_TZ,
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

const dateFmt = new Intl.DateTimeFormat("vi-VN", {
  timeZone: VN_TZ,
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

/** "27/06/2026 17:30" theo giờ VN. */
export function formatDateTimeVN(iso: string): string {
  const d = parseServerDate(iso);
  return isNaN(d.getTime()) ? "" : dateTimeFmt.format(d);
}

/** "27/06/2026" theo giờ VN. */
export function formatDateVN(iso: string): string {
  const d = parseServerDate(iso);
  return isNaN(d.getTime()) ? "" : dateFmt.format(d);
}

/** Thời gian tương đối ngắn gọn ("vừa xong", "5 phút trước", "3 ngày trước"). */
export function fromNowVN(iso: string): string {
  const d = parseServerDate(iso);
  if (isNaN(d.getTime())) return "";
  const diff = Date.now() - d.getTime();
  const min = Math.floor(diff / 60000);
  if (min < 1) return "vừa xong";
  if (min < 60) return `${min} phút trước`;
  const hours = Math.floor(min / 60);
  if (hours < 24) return `${hours} giờ trước`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days} ngày trước`;
  return formatDateVN(iso);
}
