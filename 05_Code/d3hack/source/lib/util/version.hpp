#pragma once

#include <program/version.hpp>

namespace exl::util {

    namespace impl {
        extern UserVersion s_UserVersion;
        void InitVersion();
    }

    inline UserVersion GetUserVersion() { return impl::s_UserVersion; }

    /* Game build string of the image we are running inside. */
    inline const char *GetClientVersionString() { return D3CLIENT_VER; }
}