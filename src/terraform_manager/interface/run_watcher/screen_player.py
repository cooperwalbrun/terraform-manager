import sys

from asciimatics.exceptions import ResizeScreenError
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from terraform_manager.interface.run_watcher.active_runs_view import ActiveRunsView
from terraform_manager.interface.run_watcher.active_runs_view_shared_state import \
    ActiveRunsViewSharedState


def screen_player(screen: Screen, state: ActiveRunsViewSharedState) -> None:  # pragma: no cover
    """
    Uses asciimatics to run the "Scenes" needed to create the run watcher TUI.

    :param screen: The Screen object passed to this function by asciimatics.
    :param state: The shared state entity that will always be the same for every call to this
                  method.
    :return: None.
    """

    screen.clear()
    active_runs_frame = ActiveRunsView(state, screen, minimum_seconds_between_fetches=12.0)
    # Setting the duration to 10 will force asciimatic to re-render the scene twice per second
    # (there are about 20 frames per second), but the API calls will NOT happen that frequently;
    # see minimum_seconds_between_fetches above
    scenes = [Scene([active_runs_frame], duration=10, clear=False, name="main")]
    screen.play(scenes, stop_on_resize=True, repeat=True)


def run_watcher_loop(state: ActiveRunsViewSharedState) -> None:  # pragma: no cover
    """
    Launches an infinite loop to execute the run watcher TUI, only exiting when a KeyboardInterrupt
    is caught.

    :param state: A shared state entity to pass to the downstream view object (ActiveRunsView).
    :return: None.
    """

    while True:
        try:
            Screen.wrapper(screen_player, arguments=[state])
        except ResizeScreenError:
            # We simply need to re-run Screen.wrapper() when this happens, which will happen
            # automatically during the next iteration of this infinite loop
            continue
        except KeyboardInterrupt:  # This is thrown when the program is interrupted by the user
            sys.exit(0)
