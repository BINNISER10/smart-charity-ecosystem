import { redirect } from "next/navigation";
import { cookies } from "next/headers";

export default function RootPage() {
  const token = cookies().get("scs_token")?.value;
  const role  = cookies().get("scs_role")?.value;

  if (!token) redirect("/login");
  if (role === "field_worker") redirect("/field-worker");
  redirect("/admin");
}
