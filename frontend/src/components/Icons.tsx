// Maple icon set — warm, friendly, rounded line/stroke SVGs.
import type { ReactNode } from "react";

interface IcProps {
  size?: number;
  sw?: number;
  className?: string;
}

function Ic({
  size = 20,
  sw = 1.8,
  fill = "none",
  children,
  vb = "0 0 24 24",
  className,
}: IcProps & { fill?: string; children: ReactNode; vb?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox={vb}
      fill={fill}
      stroke="currentColor"
      strokeWidth={sw}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
    >
      {children}
    </svg>
  );
}

export const IconMaple = ({ size = 24, className }: IcProps) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="currentColor"
    aria-hidden="true"
    className={className}
  >
    <path d="M12 2.2c.32 0 .6.22.68.53l.86 3.3 2.2-1.5a.7.7 0 0 1 1.08.7l-.5 2.27 2.5-.42a.7.7 0 0 1 .68 1.07l-1.7 2.36 2.1.9a.62.62 0 0 1 .04 1.12l-2.32 1.2 1.04 1.5a.6.6 0 0 1-.6.93l-3.3-.56.36 2.2a.6.6 0 0 1-.94.58l-1.7-1.2-.02 2.9a.62.62 0 0 1-1.24 0l-.02-2.9-1.7 1.2a.6.6 0 0 1-.94-.58l.36-2.2-3.3.56a.6.6 0 0 1-.6-.93l1.04-1.5-2.32-1.2a.62.62 0 0 1 .04-1.12l2.1-.9-1.7-2.36a.7.7 0 0 1 .68-1.07l2.5.42-.5-2.27a.7.7 0 0 1 1.08-.7l2.2 1.5.86-3.3A.7.7 0 0 1 12 2.2Z" />
  </svg>
);

export const IconSend = (p: IcProps) => (
  <Ic {...p}>
    <path d="M4.5 12h13M11 5.5 17.5 12 11 18.5" />
  </Ic>
);
export const IconPaperclip = (p: IcProps) => (
  <Ic {...p}>
    <path d="M18 7.5 9.6 16a3 3 0 0 1-4.24-4.24l8.3-8.3a2 2 0 0 1 2.83 2.83l-8.13 8.1a1 1 0 0 1-1.42-1.42l7.2-7.16" />
  </Ic>
);
export const IconMic = (p: IcProps) => (
  <Ic {...p}>
    <rect x="9" y="3" width="6" height="11" rx="3" />
    <path d="M5.5 11.5a6.5 6.5 0 0 0 13 0M12 18v3" />
  </Ic>
);
export const IconPlus = (p: IcProps) => (
  <Ic {...p}>
    <path d="M12 5v14M5 12h14" />
  </Ic>
);
export const IconSidebar = (p: IcProps) => (
  <Ic {...p}>
    <rect x="3.5" y="4.5" width="17" height="15" rx="2.5" />
    <path d="M9.5 4.5v15" />
  </Ic>
);
export const IconSun = (p: IcProps) => (
  <Ic {...p}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2.5v2M12 19.5v2M4.6 4.6l1.4 1.4M18 18l1.4 1.4M2.5 12h2M19.5 12h2M4.6 19.4 6 18M18 6l1.4-1.4" />
  </Ic>
);
export const IconMoon = (p: IcProps) => (
  <Ic {...p}>
    <path d="M19 14.5A8 8 0 0 1 9.5 5a7 7 0 1 0 9.5 9.5Z" />
  </Ic>
);
export const IconSearch = (p: IcProps) => (
  <Ic {...p}>
    <circle cx="11" cy="11" r="6.5" />
    <path d="m20 20-3.5-3.5" />
  </Ic>
);
export const IconCopy = (p: IcProps) => (
  <Ic {...p}>
    <rect x="9" y="9" width="11" height="11" rx="2.5" />
    <path d="M5 15H4.5A1.5 1.5 0 0 1 3 13.5v-9A1.5 1.5 0 0 1 4.5 3h9A1.5 1.5 0 0 1 15 4.5V5" />
  </Ic>
);
export const IconCheck = (p: IcProps) => (
  <Ic {...p}>
    <path d="M5 12.5 10 17.5 19 6.5" />
  </Ic>
);
export const IconEdit = (p: IcProps) => (
  <Ic {...p}>
    <path d="M14.5 5.5 18.5 9.5M4 20l1-4L16.5 4.5a2 2 0 0 1 2.83 0l.17.17a2 2 0 0 1 0 2.83L8 19l-4 1Z" />
  </Ic>
);
export const IconTrash = (p: IcProps) => (
  <Ic {...p}>
    <path d="M4.5 6.5h15M9 6.5V5a1.5 1.5 0 0 1 1.5-1.5h3A1.5 1.5 0 0 1 15 5v1.5M6 6.5 6.8 19a2 2 0 0 0 2 1.9h6.4a2 2 0 0 0 2-1.9L18 6.5" />
  </Ic>
);
export const IconThumbUp = (p: IcProps) => (
  <Ic {...p}>
    <path d="M7 10v10H4.5A.5.5 0 0 1 4 19.5v-9a.5.5 0 0 1 .5-.5H7Z" />
    <path d="M7 10l4-7a2 2 0 0 1 2 2v3h5.2a2 2 0 0 1 2 2.4l-1.3 6a2 2 0 0 1-2 1.6H7" />
  </Ic>
);
export const IconThumbDown = (p: IcProps) => (
  <Ic {...p}>
    <path d="M7 14V4H4.5A.5.5 0 0 0 4 4.5v9a.5.5 0 0 0 .5.5H7Z" />
    <path d="M7 14l4 7a2 2 0 0 0 2-2v-3h5.2a2 2 0 0 0 2-2.4l-1.3-6a2 2 0 0 0-2-1.6H7" />
  </Ic>
);
export const IconRefresh = (p: IcProps) => (
  <Ic {...p}>
    <path d="M20 8a8 8 0 0 0-14-3L4 7M4 4v3h3" />
    <path d="M4 16a8 8 0 0 0 14 3l2-2M20 20v-3h-3" />
  </Ic>
);
export const IconClose = (p: IcProps) => (
  <Ic {...p}>
    <path d="M6 6l12 12M18 6 6 18" />
  </Ic>
);
export const IconStop = (p: IcProps) => (
  <Ic {...p}>
    <rect x="6.5" y="6.5" width="11" height="11" rx="2.5" fill="currentColor" stroke="none" />
  </Ic>
);
export const IconChevron = (p: IcProps) => (
  <Ic {...p}>
    <path d="M9 6l6 6-6 6" />
  </Ic>
);
export const IconFile = (p: IcProps) => (
  <Ic {...p}>
    <path d="M13 3.5H7A1.5 1.5 0 0 0 5.5 5v14A1.5 1.5 0 0 0 7 20.5h10A1.5 1.5 0 0 0 18.5 19V9L13 3.5Z" />
    <path d="M13 3.5V9h5.5" />
  </Ic>
);
export const IconUpload = (p: IcProps) => (
  <Ic {...p}>
    <path d="M12 16V4M7 9l5-5 5 5M4.5 16v2.5A1.5 1.5 0 0 0 6 20h12a1.5 1.5 0 0 0 1.5-1.5V16" />
  </Ic>
);
export const IconPin = (p: IcProps) => (
  <Ic {...p}>
    <path d="M8 4.5h8M9.5 4.5v4l-2 3v1.5h9V11.5l-2-3v-4M12 14v5.5" />
  </Ic>
);
export const IconChat = (p: IcProps) => (
  <Ic {...p}>
    <path d="M20 11.5a7.5 7.5 0 0 1-10.5 6.86L4 20l1.64-5.5A7.5 7.5 0 1 1 20 11.5Z" />
  </Ic>
);
export const IconUsers = (p: IcProps) => (
  <Ic {...p}>
    <circle cx="9" cy="8" r="3.2" />
    <path d="M3.5 19a5.5 5.5 0 0 1 11 0M16 5.5a3 3 0 0 1 0 5.8M16.5 19a5.5 5.5 0 0 0-2-4.3" />
  </Ic>
);
export const IconBook = (p: IcProps) => (
  <Ic {...p}>
    <path d="M4 4.5h8a3 3 0 0 1 3 3V20a2.5 2.5 0 0 0-2.5-2.5H4Z" />
    <path d="M20 4.5h-3a3 3 0 0 0-3 3V20a2.5 2.5 0 0 1 2.5-2.5H20Z" />
  </Ic>
);
export const IconLogout = (p: IcProps) => (
  <Ic {...p}>
    <path d="M9 20H5.5A1.5 1.5 0 0 1 4 18.5v-13A1.5 1.5 0 0 1 5.5 4H9M15 8l4 4-4 4M19 12H9" />
  </Ic>
);
export const IconQuote = (p: IcProps) => (
  <Ic {...p}>
    <path d="M9 7H5.5A1.5 1.5 0 0 0 4 8.5V12a1.5 1.5 0 0 0 1.5 1.5H7v.5a3 3 0 0 1-3 3M19 7h-3.5A1.5 1.5 0 0 0 14 8.5V12a1.5 1.5 0 0 0 1.5 1.5H17v.5a3 3 0 0 1-3 3" />
  </Ic>
);
export const IconQuiz = (p: IcProps) => (
  <Ic {...p}>
    <rect x="5" y="3.5" width="14" height="17" rx="2.5" />
    <path d="M9 3.5h6v2.5H9zM8.5 12l2 2 4-4" />
  </Ic>
);
export const IconSpark = (p: IcProps) => (
  <Ic {...p}>
    <path d="M12 3.5l1.8 4.7L18.5 10l-4.7 1.8L12 16.5l-1.8-4.7L5.5 10l4.7-1.8L12 3.5Z" />
    <path d="M19 16l.7 1.8L21.5 18.5l-1.8.7L19 21l-.7-1.8L16.5 18.5l1.8-.7L19 16Z" />
  </Ic>
);
export const IconRoom = (p: IcProps) => (
  <Ic {...p}>
    <path d="M3.5 20.5h17M5.5 20.5V5a1.5 1.5 0 0 1 1.5-1.5h10A1.5 1.5 0 0 1 18.5 5v15.5" />
    <path d="M9 7.5h2.5M9 11h2.5M13.5 20.5v-4.5a1 1 0 0 1 1-1h1a1 1 0 0 1 1 1v4.5" />
  </Ic>
);
export const IconUserPlus = (p: IcProps) => (
  <Ic {...p}>
    <circle cx="10" cy="8" r="3.5" />
    <path d="M4 19.5c.7-3 3.2-4.5 6-4.5s5.3 1.5 6 4.5M18.5 8.5v5M16 11h5" />
  </Ic>
);
export const IconChart = (p: IcProps) => (
  <Ic {...p}>
    <path d="M4 4.5v15h16" />
    <path d="M8.5 15.5v-4M12.5 15.5v-7M16.5 15.5v-2.5" />
  </Ic>
);
