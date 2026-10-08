#pragma once

#include "common.hpp"
#include <array>
#include <tuple>

#include "version.hpp"

namespace exl::reloc {
    using VersionType = util::UserVersion;

    template<VersionType Version, impl::LookupEntry... Entries>
    using UserTableType = VersionedTable<Version, Entries...>;

    // Versioned offset lookup tables
    //
    // Key naming:
    // - Hooks/Symbols: "sym_<name>" (see `source/program/symbols/`)
    // - Globals/Pointers: descriptive keys like "app_globals"
    //
    // Adding a new supported game build:
    // 1) Add a new `util::UserVersion` enum value in `source/program/version.hpp`.
    // 2) Update `DetermineUserVersion()` to return it.
    // 3) Add a new `UserTableType<VersionType::YOUR_VERSION, ...>` table here.
    // 4) Keep `DEFAULT` pinned to the current baseline (2.7.6.90885) and only override
    //    entries that change for the new version.
    //
    // NOTE: Resolution hack offsets/logic are intentionally excluded from this table.
    // clang-format off
    using UserTableSet = TableSet<VersionType,
        /* DEFAULT is bound to D3CLIENT_VER via DetermineUserVersion(). */
        UserTableType<VersionType::DEFAULT,
            /* Early hooks (main module). */
            { util::ModuleIndex::Main, 0x480, "sym_main_init" },
            { util::ModuleIndex::Main, 0x298BD0, "sym_gfx_init" },
            { util::ModuleIndex::Main, 0x42E30, "sym_scheck_gfx_ready" },
            { util::ModuleIndex::Main, 0x4CACA0, "sym_game_common_data_init" },
            { util::ModuleIndex::Main, 0x667930, "sym_shell_initialize" },
            { util::ModuleIndex::Main, 0x7B09A0, "sym_sgame_initialize" },
            { util::ModuleIndex::Main, 0x8128A0, "sym_sinitialize_world" },

            /* Utility hooks (main module). */
            { util::ModuleIndex::Main, 0x758100, "sym_cmd_line_parse" },
            { util::ModuleIndex::Main, 0x3CC74, "sym_var_res_label" },
            { util::ModuleIndex::Main, 0xC8000, "sym_move_speed" },
            { util::ModuleIndex::Main, 0x6CC700, "sym_attack_speed" },
            { util::ModuleIndex::Main, 0xBB5E8, "sym_floating_dmg" },
            { util::ModuleIndex::Main, 0x3FEE8, "sym_font_string_get_rendered_size" },
            { util::ModuleIndex::Main, 0x3FF50, "sym_font_string_draw_03ff50" },
            { util::ModuleIndex::Main, 0x3E5B0, "sym_font_string_draw_03e5b0" },
            { util::ModuleIndex::Main, 0x10C8, "sym_font_string_draw_0010c8" },

            /* Season/event hooks (main module). */
            { util::ModuleIndex::Main, 0x641F0, "sym_OnConfigFileRetrieved" },
            { util::ModuleIndex::Main, 0x65270, "sym_OnSeasonsFileRetrieved" },
            { util::ModuleIndex::Main, 0x657F0, "sym_OnBlacklistFileRetrieved" },
            { util::ModuleIndex::Main, 0x1B0600, "sym_MailCheckLobbyConnection" },

            /* Lobby hooks (main module). */
            { util::ModuleIndex::Main, 0x60810, "sym_lobby_service_idle_internal" },
            { util::ModuleIndex::Main, 0x6065C, "sym_lobby_service_create" },
            { util::ModuleIndex::Main, 0x1BD030, "sym_set_game_params_for_hero" },
            { util::ModuleIndex::Main, 0x8951B0, "sym_specifiers_from_modifier" },
            { util::ModuleIndex::Main, 0x896908, "sym_eval_mod" },
            { util::ModuleIndex::Main, 0x495CC0, "sym_dupe_dropped_item" },
            { util::ModuleIndex::Main, 0xBF630, "sym_request_drop_item" },

            /* Debugging hooks (main module). */
            { util::ModuleIndex::Main, 0x185AA0, "sym_print_challenge_rift_failed" },
            { util::ModuleIndex::Main, 0x185F70, "sym_challenge_rift_callback" },
            { util::ModuleIndex::Main, 0x6A2A8, "sym_pubfile_data_hex" },
            { util::ModuleIndex::Main, 0xA2AD60, "sym_print_error_display" },
            { util::ModuleIndex::Main, 0xA2AD70, "sym_print_error" },
            { util::ModuleIndex::Main, 0xA2AF14, "sym_print_error_string" },
            { util::ModuleIndex::Main, 0xA2AF74, "sym_print_error_string_final" },
            { util::ModuleIndex::Main, 0x4B114C, "sym_count_cosmetics" },
            { util::ModuleIndex::Main, 0xBFD9A0, "sym_parse_file" },
            { util::ModuleIndex::Main, 0x3A7418, "sym_font_snoop" },
            { util::ModuleIndex::Main, 0x69BAE0, "sym_store_attrib_defs" },
            { util::ModuleIndex::Main, 0x6B5484, "sym_print_saved_attribs" },

            /* Globals (main module). */
            { util::ModuleIndex::Main, 0x17DE610, "main_rwindow" },
            { util::ModuleIndex::Main, 0x1830F68, "gfx_internal_data_ptr" },
            { util::ModuleIndex::Main, 0x114C970, "gfx_nvn_globals_ptr" },
            { util::ModuleIndex::Main, 0x1905610, "app_globals" },
            { util::ModuleIndex::Main, 0x114AC90, "lobby_services_ptr" },
            { util::ModuleIndex::Main, 0x191CA70, "sigma_thread_data" },
            { util::ModuleIndex::Main, 0x1A5F1B8, "sigma_globals" },
            { util::ModuleIndex::Main, 0x191EAD8, "attrib_defs" },
            { util::ModuleIndex::Main, 0x1154B68, "item_invalid" },
            { util::ModuleIndex::Main, 0x1A39CF0, "world_place_null" },
            { util::ModuleIndex::Main, 0x1A5F108, "refstring_data_buffer_nil" },
            { util::ModuleIndex::Main, 0x1A63CEC, "unicode_text_current_locale" },
            { util::ModuleIndex::Main, 0x114A5A0, "gb_dev_mem_mode_ptr" },
            { util::ModuleIndex::Main, 0x114A5A8, "system_allocator_ptr" },
            { util::ModuleIndex::Main, 0x115A560, "sigma_local_heap_ptr" },
            { util::ModuleIndex::Main, 0x1150E08, "sigma_heap_limit_ptr" },
            { util::ModuleIndex::Main, 0x1150E10, "sigma_heap_ptr_0" },
            { util::ModuleIndex::Main, 0x11572D0, "sigma_virtual_heap_ptr" },
            { util::ModuleIndex::Main, 0x114C968, "sigma_remote_heap_ptr_0" },
            { util::ModuleIndex::Main, 0x114C9A0, "sigma_remote_heap_ptr_1" },
            { util::ModuleIndex::Main, 0x114C990, "nx64_nvn_heap_ptr" },
            { util::ModuleIndex::Main, 0x114C998, "nx64_nvn_heap_ptr_alias" },
            { util::ModuleIndex::Main, 0x1A50690, "sigma_heap_block_0" },
            { util::ModuleIndex::Main, 0x1A50698, "sigma_virtual_heap_block" },
            { util::ModuleIndex::Main, 0x1A506A0, "sigma_remote_addr_0" },
            { util::ModuleIndex::Main, 0x1A506A8, "sigma_remote_heap_0" },
            { util::ModuleIndex::Main, 0x1A506B0, "sigma_remote_addr_1" },
            { util::ModuleIndex::Main, 0x1A506B8, "sigma_remote_heap_1" },

            /* Season/event request flags (main module). */
            { util::ModuleIndex::Main, 0x114AD48, "season_config_request_flag_ptr" },
            { util::ModuleIndex::Main, 0x114AD50, "season_seasons_request_flag_ptr" },
            { util::ModuleIndex::Main, 0x114AD68, "season_blacklist_request_flag_ptr" },

            /* Symbols (main module). */
            { util::ModuleIndex::Main, 0x4C4C20, "sym_GameActiveGameCommonDataIsServer" },
            { util::ModuleIndex::Main, 0x4C4CA0, "sym_GameServerCodeLeave_Tracked" },
            { util::ModuleIndex::Main, 0x4C4EF0, "sym__GameServerCodeEnter" },
            { util::ModuleIndex::Main, 0x4C7DF0, "sym_GameIsStartUp" },
            { util::ModuleIndex::Main, 0x4C7E80, "sym_ServerIsLocal" },
            { util::ModuleIndex::Main, 0x56790, "sym_GetPrimaryProfileUserIndex" },
            { util::ModuleIndex::Main, 0x7B2990, "sym_SGameGlobalsGet" },
            { util::ModuleIndex::Main, 0x4C79D0, "sym_GameGetParts" },
            { util::ModuleIndex::Main, 0x9622D0, "sym_ServerGetOnlyGameConnection" },
            { util::ModuleIndex::Main, 0x7B88D0, "sym_AppServerGetOnlyGame" },
            { util::ModuleIndex::Main, 0xC07800, "sym_bdLogSubscriber_publish" },
            { util::ModuleIndex::Main, 0x758F40, "sym_CmdLineGetParams" },
            { util::ModuleIndex::Main, 0x4C4AD0, "sym_AppDrawFlagSet" },
            { util::ModuleIndex::Main, 0xA27E30, "sym_XVarString_Set" },
            { util::ModuleIndex::Main, 0xA2C920, "sym_FileReadIntoMemory" },
            { util::ModuleIndex::Main, 0xA2CB50, "sym_FileReferenceInit" },
            { util::ModuleIndex::Main, 0xA2D130, "sym_FileCreate" },
            { util::ModuleIndex::Main, 0xA2D1F0, "sym_FileExists" },
            { util::ModuleIndex::Main, 0xA2D200, "sym_FileOpen" },
            { util::ModuleIndex::Main, 0xA2D2D0, "sym_FileClose" },
            { util::ModuleIndex::Main, 0xA2D370, "sym_FileWrite" },
            { util::ModuleIndex::Main, 0xF2BB0, "sym_sReadFile" },
            { util::ModuleIndex::Main, 0xA2C020, "sym_TraceInternal_Log" },
            { util::ModuleIndex::Main, 0xA2BC40, "sym_ErrorManagerEnableLocalLogging" },
            { util::ModuleIndex::Main, 0xA2BC60, "sym_ErrorManagerSetLogStreamDirectory" },
            { util::ModuleIndex::Main, 0xA2BC80, "sym_ErrorManagerSetLogStreamFilename" },
            { util::ModuleIndex::Main, 0xA2BCE0, "sym_ErrorManagerLogToStream" },
            { util::ModuleIndex::Main, 0x93D0, "sym_GetLocalStorage" },
            { util::ModuleIndex::Main, 0x719110, "sym_GetGameMessageTypeAndSize" },
            { util::ModuleIndex::Main, 0x1E0DF0, "sym_DisplaySeasonEndingMessage" },
            { util::ModuleIndex::Main, 0x1E0F60, "sym_DisplayLongMessageForPlayer" },
            { util::ModuleIndex::Main, 0x933FF0, "sym_DisplayGameMessageForAllPlayers" },
            { util::ModuleIndex::Main, 0xA36B50, "sym_sigma_memory_init" },
            { util::ModuleIndex::Main, 0xE7640, "sym_nx64_nvn_heap_early_init" },
            { util::ModuleIndex::Main, 0xEF300, "sym_nx64_nvn_heap_add_pool" },
            { util::ModuleIndex::Main, 0xBD6210, "sym_bdMemory_set_allocate" },
            { util::ModuleIndex::Main, 0xBD6220, "sym_bdMemory_set_deallocate" },
            { util::ModuleIndex::Main, 0xBD6230, "sym_bdMemory_set_reallocate" },
            { util::ModuleIndex::Main, 0xBD6240, "sym_bdMemory_set_aligned_allocate" },
            { util::ModuleIndex::Main, 0xBD6250, "sym_bdMemory_set_aligned_deallocate" },
            { util::ModuleIndex::Main, 0xBD6260, "sym_bdMemory_set_aligned_reallocate" },
            { util::ModuleIndex::Main, 0xC30, "sym_bdMemory_alloc" },
            { util::ModuleIndex::Main, 0xC40, "sym_bdMemory_free" },
            { util::ModuleIndex::Main, 0xC50, "sym_bdMemory_realloc" },
            { util::ModuleIndex::Main, 0xC22A30, "sym_bdMemory_calloc" },
            { util::ModuleIndex::Main, 0xC60, "sym_bdMemory_aligned_alloc" },
            { util::ModuleIndex::Main, 0xC70, "sym_bdMemory_aligned_free" },
            { util::ModuleIndex::Main, 0xC80, "sym_bdMemory_aligned_realloc" },
            { util::ModuleIndex::Main, 0x29B1E0, "sym_GfxGetDesiredDisplayMode" },
            { util::ModuleIndex::Main, 0x299FE0, "sym_GfxDeviceReset" }, 
            { util::ModuleIndex::Main, 0x299910, "sym_GfxForceDeviceReset" },
            { util::ModuleIndex::Main, 0x29B0E0, "sym_GfxWindowChangeDisplayMode" },
            { util::ModuleIndex::Main, 0xEBAC0, "sym_get_render_target_current_resolution" },
            { util::ModuleIndex::Main, 0x3D550, "sym_CGameAsyncRenderFlush" },
            { util::ModuleIndex::Main, 0x3D570, "sym_CGameAsyncRenderGPUFlush" },
            { util::ModuleIndex::Main, 0x34BEE0, "sym_SetUICConversionConstansts" },
            { util::ModuleIndex::Main, 0x333310, "sym_UI_GfxInit" },
            { util::ModuleIndex::Main, 0x29CBC0, "sym_ImageTextureFrame_ctor" },
            { util::ModuleIndex::Main, 0x34C8E0, "sym_FormatTruncatedNumber" },
            { util::ModuleIndex::Main, 0xA27060, "sym_XVarBool_ToString" },
            { util::ModuleIndex::Main, 0xA27460, "sym_XVarUint32_ToString" },
            { util::ModuleIndex::Main, 0xA26FC0, "sym_XVarBool_Set" },
            { util::ModuleIndex::Main, 0xA273C0, "sym_XVarUint32_Set" },
            { util::ModuleIndex::Main, 0xA27B50, "sym_XVarFloat_Set" },
            { util::ModuleIndex::Main, 0x66B10, "sym_StorageGetPublisherFile" },
            { util::ModuleIndex::Main, 0x185F70, "sym_sOnGetChallengeRiftData" },
            { util::ModuleIndex::Main, 0xBB2C50, "sym_ParsePartialFromString" },
            { util::ModuleIndex::Main, 0x564D00, "sym_ChallengeData_ctor" },
            { util::ModuleIndex::Main, 0x62ABE0, "sym_WeeklyChallengeData_ctor" },
            { util::ModuleIndex::Main, 0x4C8C10, "sym_GameRandRangeInt" },
            { util::ModuleIndex::Main, 0x4C8DF0, "sym_GameIsSeasonal" },
            { util::ModuleIndex::Main, 0x72E090, "sym_OnlineServiceGetSeasonNum" },
            { util::ModuleIndex::Main, 0x72E0A0, "sym_OnlineServiceGetSeasonState" },
            { util::ModuleIndex::Main, 0x574E0, "sym_ConsoleGamerProfileGetAccount" },
            { util::ModuleIndex::Main, 0x776350, "sym_OpenChallengeRift" },
            { util::ModuleIndex::Main, 0x775CD0, "sym_ChallengeRiftHandleChallengeRewards" },
            { util::ModuleIndex::Main, 0x7764E0, "sym_ChallengeRiftGrantRewardToPlayerIfEligible" },
            { util::ModuleIndex::Main, 0x4EDC0, "sym_ChallengeRiftRewardEarned_SaveToProfile" },
            { util::ModuleIndex::Main, 0xB20, "sym_rawfree" },
            { util::ModuleIndex::Main, 0xA36E20, "sym_SigmaMemoryNew" },
            { util::ModuleIndex::Main, 0xA36F70, "sym_SigmaMemoryFree" },
            { util::ModuleIndex::Main, 0xA37120, "sym_SigmaMemoryMove" },
            { util::ModuleIndex::Main, 0xA37180, "sym_op_delete_1" },
            { util::ModuleIndex::Main, 0xA371B0, "sym_op_delete_2" },
            { util::ModuleIndex::Main, 0x66690, "sym_blz_basic_string" },
            { util::ModuleIndex::Main, 0x66690, "sym_blz_string_ctor" },
            { util::ModuleIndex::Main, 0x3C390, "sym_blz_make_stringf" },
            { util::ModuleIndex::Main, 0x3C390, "sym_blz_make_stringfb" },
            { util::ModuleIndex::Main, 0x505880, "sym_sGetItemTypeString" },
            { util::ModuleIndex::Main, 0x69B330, "sym_AttribParamToString" },
            { util::ModuleIndex::Main, 0x69FCE0, "sym_FastAttribToString" },
            { util::ModuleIndex::Main, 0x69B1D0, "sym_AttribStringToParam" },
            { util::ModuleIndex::Main, 0x6CA4F0, "sym_GBIDToStringAll" },
            { util::ModuleIndex::Main, 0x6CBD70, "sym_GBIDToString" },
            { util::ModuleIndex::Main, 0x6F1580, "sym_StringListFetchLPCSTR" },
            { util::ModuleIndex::Main, 0x483DE0, "sym_ClearAssignedHero" },
            { util::ModuleIndex::Main, 0x489280, "sym_ACDInventoryItemAllowedInSlot" },
            { util::ModuleIndex::Main, 0x48E980, "sym_ACDAddToInventory" },
            { util::ModuleIndex::Main, 0x490F90, "sym_SACDInventoryPickupOrSpillOntoGround" },
            { util::ModuleIndex::Main, 0x4F45F0, "sym_ItemHasLabel" },
            { util::ModuleIndex::Main, 0x4FC220, "sym_SetBindingLevel" },
            { util::ModuleIndex::Main, 0x4FC3E0, "sym_SetRecipient" },
            { util::ModuleIndex::Main, 0x4FF420, "sym_PopulateGenerator" },
            { util::ModuleIndex::Main, 0x500000, "sym_CItemGenerate" },
            { util::ModuleIndex::Main, 0x60CCC0, "sym_ItemsGenerator_ctor" },
            { util::ModuleIndex::Main, 0x60D350, "sym_ItemsGenerator_dtor" },
            { util::ModuleIndex::Main, 0x7A34A0, "sym_FlippyFindLandingLocation" },
            { util::ModuleIndex::Main, 0x7A4B00, "sym_FlippyDropCreateOnActor" },
            { util::ModuleIndex::Main, 0x7DE2E0, "sym_SItemGenerate" },
            { util::ModuleIndex::Main, 0x802800, "sym_AddItemToInventory" },
            { util::ModuleIndex::Main, 0x890B10, "sym_LootQuickCreateItem" },
            { util::ModuleIndex::Main, 0x4B1790, "sym_GetCosmeticItemType" },
            { util::ModuleIndex::Main, 0x504CC0, "sym_ItemIsCosmeticItem" },
            { util::ModuleIndex::Main, 0x6A3E80, "sym_SetCraftLevel" },
            { util::ModuleIndex::Main, 0x6A4B20, "sym_Crafting_GetTransmogSlot" },
            { util::ModuleIndex::Main, 0x7A1E80, "sym_ExperienceSetLevel" },
            { util::ModuleIndex::Main, 0x7A1C00, "sym_ExperienceDropLootForAll" },
            { util::ModuleIndex::Main, 0x7C2D50, "sym_SCosmeticItems_LearnCosmeticItem" },
            { util::ModuleIndex::Main, 0x7C3050, "sym_SCosmeticItems_LearnPet" },
            { util::ModuleIndex::Main, 0x7E03B0, "sym_SItemPlayerExtractLegendaryPower" },
            { util::ModuleIndex::Main, 0x87FF40, "sym_SItemCrafting_TryUnlockTransmog" },
            { util::ModuleIndex::Main, 0x880C40, "sym_SItemCrafting_TryUnlockSecondaryTmogs" },
            { util::ModuleIndex::Main, 0x884A30, "sym_SCrafterIncrementLevel" },
            { util::ModuleIndex::Main, 0x884B50, "sym_SItemCrafting_LearnRecipe" },
            { util::ModuleIndex::Main, 0x886E70, "sym_sCrafterOnLevelUp" },
            { util::ModuleIndex::Main, 0x88DEE0, "sym_LootRollForAncientLegendary" },
            { util::ModuleIndex::Main, 0x4E5F50, "sym_GlobalSNOGet" },
            { util::ModuleIndex::Main, 0x6CB880, "sym_GBEnumerate" },
            { util::ModuleIndex::Main, 0x6CBDA0, "sym_GBGetHandlePool" },
            { util::ModuleIndex::Main, 0x74A610, "sym_SNOToString" },
            { util::ModuleIndex::Main, 0x933FD0, "sym_PlayerIsPrimary" },
            { util::ModuleIndex::Main, 0x93DBF0, "sym_GetPrimaryPlayer" },
            { util::ModuleIndex::Main, 0xB8740, "sym_LocalPlayerGet" },
            { util::ModuleIndex::Main, 0x51FD40, "sym_PlayerGetByACD" },
            { util::ModuleIndex::Main, 0x51D0F0, "sym_PlayerGetHeroDisplayName" },
            { util::ModuleIndex::Main, 0x51F8C0, "sym_PlayerGetFirstAll" },
            { util::ModuleIndex::Main, 0x51F970, "sym_PlayerGetNextAll" },
            { util::ModuleIndex::Main, 0x5203C0, "sym_PlayerGetFirstInGame" },
            { util::ModuleIndex::Main, 0x5212F0, "sym_PlayerGetByPlayerIndex" },
            { util::ModuleIndex::Main, 0x527AE0, "sym_GetPrimaryPlayerForGameConnection" },
            { util::ModuleIndex::Main, 0x7A6430, "sym_PlayerList_ctor" },
            { util::ModuleIndex::Main, 0x7A6620, "sym_PlayerListGetElementPool" },
            { util::ModuleIndex::Main, 0x7A6CF0, "sym_PlayerListGetSingle" },
            { util::ModuleIndex::Main, 0x7A6950, "sym_PlayerListGetAllInGame" },
            { util::ModuleIndex::Main, 0x7FD4F0, "sym_SPlayerIsLocal" },
            { util::ModuleIndex::Main, 0x46FB20, "sym_ACD_AttributesGetInt" },
            { util::ModuleIndex::Main, 0x46FB30, "sym_ACD_AttributesGetFloat" },
            { util::ModuleIndex::Main, 0x46FC00, "sym_ACD_AttributesSetInt" },
            { util::ModuleIndex::Main, 0x46FB80, "sym_ACD_AttributesSetFloat" },
            { util::ModuleIndex::Main, 0x47FFB0, "sym_ACD_ModifyCurrencyAmount" },
            { util::ModuleIndex::Main, 0x480230, "sym_ACD_SetCurrencyAmount" },
            { util::ModuleIndex::Main, 0x669CB0, "sym_ACDTryToGet" },
            { util::ModuleIndex::Main, 0x69F5E0, "sym_FastAttribGetValueInt" },
            { util::ModuleIndex::Main, 0x69F680, "sym_FastAttribGetValueFloat" },
            { util::ModuleIndex::Main, 0x69B010, "sym_KeyGetDataType" },
            { util::ModuleIndex::Main, 0x6A0250, "sym_KeyGetParamType" },
            { util::ModuleIndex::Main, 0x71DB90, "sym_MessageSendToClient" },
            { util::ModuleIndex::Main, 0x86E070, "sym_ActorGet" },
            { util::ModuleIndex::Main, 0x86F940, "sym_ActorFlagSet" },
            { util::ModuleIndex::Main, 0xA48790, "sym_CRefString_ctor_default" },
            { util::ModuleIndex::Main, 0xA487B0, "sym_CRefString_ctor_int" },
            { util::ModuleIndex::Main, 0xA487D0, "sym_CRefString_ctor_cref" },
            { util::ModuleIndex::Main, 0xA48800, "sym_CRefString_ctor_lpcstr" },
            { util::ModuleIndex::Main, 0xA48890, "sym_CRefString_CommonCtorBody" },
            { util::ModuleIndex::Main, 0xA489B0, "sym_CRefString_ReAllocate" },
            { util::ModuleIndex::Main, 0xA48BB0, "sym_CRefString_Free" },
            { util::ModuleIndex::Main, 0xA48D80, "sym_CRefString_Allocate" },
            { util::ModuleIndex::Main, 0xA48F10, "sym_CRefString_dtor" },
            { util::ModuleIndex::Main, 0xA491A0, "sym_CRefString_op_eq_cref" },
            { util::ModuleIndex::Main, 0xA49200, "sym_CRefString_op_eq_cref_assign" },
            { util::ModuleIndex::Main, 0xA492D0, "sym_CRefString_op_eq_lpcstr" },
            { util::ModuleIndex::Main, 0xA493C0, "sym_CRefString_op_add_eq_lpcstr" },
            { util::ModuleIndex::Main, 0xA49470, "sym_CRefString_Append" },
            { util::ModuleIndex::Main, 0xA4A370, "sym_XLocaleToString" },

            // Patch-only offsets/patch-sites (main module).
            // See `source/program/offsets_patch_only.inl` (includes resolution hack entries).
            #include "offsets_patch_only.inl"

            /* Unused/debug offsets (main module). */
            { util::ModuleIndex::Main, 0x7EAD18, "hook_lobby_store_player_pointers_007eac18" },  // unused
            { util::ModuleIndex::Main, 0xB7DCC, "hook_lobby_new_player_msg_000b7dcc" },  // unused
            { util::ModuleIndex::Main, 0x7B19B8, "hook_lobby_sgame_get_007b18b8" },  // unused
            { util::ModuleIndex::Main, 0x488F30, "hook_lobby_return_true_00488ec0" },  // unused
            { util::ModuleIndex::Main, 0x488C10, "hook_lobby_return_true_00488ba0" },  // unused
            { util::ModuleIndex::Main, 0x504FE0, "hook_lobby_return_true_00504ee0" },  // unused
            { util::ModuleIndex::Main, 0xA2AD70, "hook_print_error" },  // unused
            { util::ModuleIndex::Main, 0xA2AF14, "hook_print_error_string" },  // unused
            { util::ModuleIndex::Main, 0x4B114C, "hook_debug_count_cosmetics_004b104c" },  // unused
            { util::ModuleIndex::Main, 0xBFD9A0, "hook_debug_parse_file_00bfd8a0" },  // unused
            { util::ModuleIndex::Main, 0xC593D4, "hook_debug_curl_data_00c592d4" },  // unused
            { util::ModuleIndex::Main, 0x3A7418, "hook_debug_font_snoop_003a73a8" },  // unused
            { util::ModuleIndex::Main, 0x69BAE0, "hook_debug_store_attrib_defs_0069b9e0" },  // unused
            { util::ModuleIndex::Main, 0x6B5484, "hook_debug_print_saved_attribs_006b5384" }  // unused
        >
    >;
    // clang-format on
}  // namespace exl::reloc

namespace d3::offsets {
    // Minimal set of lookup keys required to safely install boot hooks and bring up the overlay.
    // Keep this list small and focused: optional features should not hard-fail boot.
    inline constexpr std::array<const char *, 8> kRequiredBootLookupKeys = {
        "sym_main_init",
        "sym_gfx_init",
        "sym_shell_initialize",
        "sym_game_common_data_init",
        "sym_sinitialize_world",

        "main_rwindow",
        "gfx_internal_data_ptr",
        "unicode_text_current_locale",
    };
}  // namespace d3::offsets
