import Lean
import Lean.Replay

open Lean

partial def auditAxioms (env : Environment) (name : Name) : StateM NameSet (List String) := do
  if (← get).contains name then return []
  modify (·.insert name)
  let some info := env.find? name | return [s!"unknown:{name}"]
  let mut axioms := match info with
    | .axiomInfo _ => [name.toString]
    | _ => []
  for dependency in info.getUsedConstantsAsSet do
    axioms := axioms ++ (← auditAxioms env dependency)
  return axioms

unsafe def main (args : List String) : IO UInt32 := do
  let [proofFile, target, expectedFile, library] := args | throw <| IO.userError "Invalid checker arguments"
  let name := target.toName
  let (submitted, _) ← readModuleData proofFile
  -- Start with the shipped library. Replay only kernel declarations from the
  -- candidate, without loading its syntax, options or environment extensions.
  let imports : Array Import := #[{module := `Lean}, {module := `Lake}]
  let imports := if library == "mathlib" then imports.push {module := `Mathlib} else imports
  let base ← importModules imports {}
  let constants := submitted.constants.foldl (fun m info => m.insert info.name info) ({} : HashMap Name ConstantInfo)
  let checked ← base.replay constants
  let some (.thmInfo proof) := checked.find? name
    | throw <| IO.userError "The candidate must define the requested theorem"
  unless constants.contains name do
    throw <| IO.userError "The candidate must define the requested theorem"
  let axioms := Id.run ((auditAxioms checked name).run' {})
  let mut statementMatches := false
  if expectedFile != "" then
    let (expected, _) ← readModuleData expectedFile
    let some signature := expected.constants.find? (·.name == `localToolkitStatement)
      | throw <| IO.userError "Expected proposition did not define a type"
    let alias := `localToolkitStatementKernelCheck
    if signature.levelParams.length == proof.levelParams.length then
      let binding := mkConst name (signature.levelParams.map Level.param)
      match checked.addDecl {} (.thmDecl {
          name := alias, levelParams := signature.levelParams,
          type := signature.type, value := binding, all := [alias]
        }) with
      | .ok _ => statementMatches := true
      | .error _ => pure ()
  IO.println <| (Json.mkObj [
    ("axioms", toJson axioms), ("statement_matches", toJson statementMatches)
  ]).compress
  return 0
