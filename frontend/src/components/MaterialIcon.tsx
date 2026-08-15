import { useState } from "react";

interface MaterialIconProps {
  slug: string;
  name: string;
}

export function MaterialIcon({ slug, name }: MaterialIconProps) {
  const [missing, setMissing] = useState(false);
  if (missing) {
    return <div className="material-icon material-icon--missing" aria-hidden="true" />;
  }
  return (
    <img
      className="material-icon"
      src={`/materials/${slug}.svg`}
      alt={name}
      onError={() => setMissing(true)}
    />
  );
}
