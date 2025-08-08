# Systematic Refactoring Plan - 5,383 Errors

## Error Distribution Analysis
**Total Errors:** 5,383 across 241 source files

### Phase 1: Quick Wins (710 errors - 13%)
- **reportUnusedImport** (402) - Remove dead imports
- **reportDeprecated** (308) - Replace `datetime.utcnow()` with `datetime.now(timezone.utc)`

### Phase 2: Core Type Foundation (2,380 errors - 44%) 
- **reportUnknownMemberType** (926) - Add type annotations for object attributes
- **reportUnknownVariableType** (868) - Add variable type annotations  
- **reportUnknownArgumentType** (702) - Fix function argument types
- **reportArgumentType** (450) - Fix type mismatches in arguments
- **reportUnknownParameterType** (410) - Add parameter type annotations

### Phase 3: Advanced Type Issues (2,293 errors - 43%)
- **reportAttributeAccessIssue** (236) - Fix attribute access on unknown types
- **reportGeneralTypeIssues** (196) - Complex type compatibility issues
- **reportCallIssue** (189) - Function call argument mismatches  
- **reportMissingParameterType** (182) - Missing parameter annotations
- **reportMissingTypeArgument** (77) - Generic type arguments
- **Other categories** (1,413) - Various specific issues

## Target Files by Error Density
*Top 20 files with most errors (to be determined in next analysis)*

## Execution Strategy
1. **Start with Phase 1** - Remove unused imports and fix deprecated calls
2. **Build type foundation** - Add core type annotations systematically
3. **Resolve complex issues** - Handle inheritance, generics, and edge cases
4. **Validate progress** - Run pyright after each major fix batch

## Success Metrics
- Target: Reduce from 5,383 to under 100 errors
- Phase 1 target: 4,673 errors remaining
- Phase 2 target: 2,293 errors remaining  
- Phase 3 target: Under 100 errors remaining

**Next Action:** Identify highest-error-density files for targeted fixes
