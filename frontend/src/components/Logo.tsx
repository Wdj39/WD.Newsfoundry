import { Bot } from "lucide-react";

type LogoProps = {
  size?: "md" | "lg";
};

/** Logo NewsFoundry : texte violet en capitales + icône robot. */
export default function Logo({ size = "md" }: LogoProps) {
  const textSize = size === "lg" ? "text-xl" : "text-base";
  const iconSize = size === "lg" ? 18 : 14;

  return (
    <span className={`inline-flex items-center gap-1 font-medium text-primary ${textSize}`}>
      NEWSFOUNDRY
      <Bot size={iconSize} aria-hidden="true" />
    </span>
  );
}
