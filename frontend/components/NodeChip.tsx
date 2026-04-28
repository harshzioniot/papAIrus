import { NodeOut } from "@/lib/api";

const TYPE_STYLE: Record<string, { bg: string; color: string; border: string }> = {
  emotion:  { bg: "var(--purple-bg)", color: "var(--purple)", border: "var(--purple-border)" },
  person:   { bg: "var(--blue-bg)",   color: "var(--blue)",   border: "var(--blue-border)"   },
  theme:    { bg: "var(--teal-bg)",   color: "var(--teal)",   border: "var(--teal-border)"   },
  habit:    { bg: "var(--amber-bg)",  color: "var(--amber)",  border: "var(--amber-border)"  },
  event:    { bg: "var(--purple-bg)", color: "var(--purple)", border: "var(--purple-border)" },
  place:    { bg: "var(--teal-bg)",   color: "var(--teal2)",  border: "var(--teal-border)"   },
  decision: { bg: "var(--coral-bg)",  color: "var(--coral)",  border: "var(--coral-border)"  },
  outcome:  { bg: "var(--blue-bg)",   color: "var(--blue)",   border: "var(--blue-border)"   },
};

interface Props {
  node: Pick<NodeOut, "name" | "type">;
  onRemove?: () => void;
}

export default function NodeChip({ node, onRemove }: Props) {
  const s = TYPE_STYLE[node.type] ?? TYPE_STYLE.theme;
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        padding: "3px 10px",
        borderRadius: 12,
        fontSize: 11,
        fontWeight: 500,
        background: s.bg,
        color: s.color,
        border: `1px solid ${s.border}`,
      }}
    >
      {node.name}
      {onRemove && (
        <button
          onClick={onRemove}
          style={{
            background: "none",
            border: "none",
            color: s.color,
            cursor: "pointer",
            fontSize: 12,
            lineHeight: 1,
            padding: 0,
            opacity: 0.6,
          }}
        >
          ×
        </button>
      )}
    </span>
  );
}
