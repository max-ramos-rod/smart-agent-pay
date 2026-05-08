type Props = { data: number[]; width?: number; height?: number };

export function Sparkline({ data, width = 600, height = 120 }: Props) {
  if (data.length < 2) return <svg width={width} height={height} />;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const stepX = width / (data.length - 1);
  const points = data
    .map((v, i) => `${i * stepX},${height - ((v - min) / range) * height}`)
    .join(" ");

  const last = data[data.length - 1];
  const first = data[0];
  const up = last >= first;
  const stroke = up ? "hsl(var(--primary))" : "hsl(var(--destructive))";

  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id="sparkFill" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={stroke} stopOpacity="0.35" />
          <stop offset="100%" stopColor={stroke} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polyline
        fill="url(#sparkFill)"
        stroke="none"
        points={`0,${height} ${points} ${width},${height}`}
      />
      <polyline fill="none" stroke={stroke} strokeWidth="2.5" points={points} strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}
