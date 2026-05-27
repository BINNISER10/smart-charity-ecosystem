import { redirect } from "next/navigation";
import { cookies } from "next/headers";

export default async function RootPage() {
  const store = await cookies();
  const token = store.get("scs_token")?.value;
  const role  = store.get("scs_role")?.value;

  if (!token) redirect("/login");
  if (role === "field_worker") redirect("/field-worker");
  redirect("/admin");
}
