import os
import json
import numpy as np
import marshmallow
from argschema import ArgSchemaParser
from argschema.utils import schema_argparser
import warnings
import matplotlib
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402
from ._schemas import InputParameters, OutputParameters  # noqa: E402
from .eye_tracking import EyeTracker  # noqa: E402
from .frame_stream import CvInputStream, CvOutputStream  # noqa: E402
from .plotting import (plot_summary, plot_cumulative,
                       annotate_with_box)  # noqa: E402
from .feature_extraction import get_filter  # noqa: E402


def setup_annotation(im_shape, annotate_movie, output_file, fourcc="H264"):
    if annotate_movie:
        ostream = CvOutputStream(output_file, im_shape[::-1], fourcc=fourcc)
        ostream.open(output_file)
    else:
        ostream = None
    return ostream


def write_output(output_dir, cr_parameters, pupil_parameters, mean_frame):
    output = {
        "cr_parameter_file": os.path.join(output_dir, "cr_params.npy"),
        "pupil_parameter_file": os.path.join(output_dir, "pupil_params.npy"),
        "mean_frame_file": os.path.join(output_dir, "mean_frame.png")
    }
    plt.imsave(output["mean_frame_file"], mean_frame, cmap="gray")
    np.save(output["cr_parameter_file"], cr_parameters)
    np.save(output["pupil_parameter_file"], pupil_parameters)
    return output


def write_QC_output(annotator, cr_parameters, pupil_parameters,
                    mean_frame, **kwargs):
    output_dir = kwargs["qc"]["output_dir"]
    annotator.annotate_with_cumulative_cr(
        mean_frame, os.path.join(output_dir, "cr_all.png"))
    annotator.annotate_with_cumulative_pupil(
        mean_frame, os.path.join(output_dir, "pupil_all.png"))
    plot_cumulative(annotator.densities["pupil"], annotator.densities["cr"],
                    output_dir=output_dir)
    plot_summary(pupil_parameters, cr_parameters, output_dir=output_dir)
    pupil_bbox = kwargs.get("pupil_bounding_box", [])
    cr_bbox = kwargs.get("cr_bounding_box", [])
    if len(pupil_bbox) == 4:
        mean_frame = annotate_with_box(mean_frame, pupil_bbox,
                                       (0, 0, 255))
    if len(cr_bbox) == 4:
        mean_frame = annotate_with_box(mean_frame, cr_bbox,
                                       (255, 0, 0))
    plt.imsave(os.path.join(output_dir, "mean_frame_bbox.png"), mean_frame)


def get_starburst_args(kwargs):
    starburst_args = kwargs.copy()
    threshold_factor = starburst_args.pop("threshold_factor", None)
    threshold_pixels = starburst_args.pop("threshold_pixels", None)

    if starburst_args.get("cr_threshold_factor", None) is None:
        starburst_args["cr_threshold_factor"] = threshold_factor
    if starburst_args.get("pupil_threshold_factor", None) is None:
        starburst_args["pupil_threshold_factor"] = threshold_factor

    if starburst_args.get("cr_threshold_pixels", None) is None:
        starburst_args["cr_threshold_pixels"] = threshold_pixels
    if starburst_args.get("pupil_threshold_pixels", None) is None:
        starburst_args["pupil_threshold_pixels"] = threshold_pixels

    return starburst_args


def load_prefilter(kwargs):
    if kwargs.get("apply_prefilter", False):
        return get_filter(kwargs.get("prefilter_class"),
                          **kwargs.get("prefilter_kwargs", {}))
    return None


def main():
    """Main entry point for running AllenSDK Eye Tracking."""
    try:
        mod = ArgSchemaParser(schema_type=InputParameters,
                              output_schema_type=OutputParameters)

        starburst_args = get_starburst_args(mod.args["starburst"])

        istream = CvInputStream(mod.args["input_source"])

        im_shape = istream.frame_shape

        ostream = setup_annotation(im_shape, **mod.args["annotation"])

        prefilter = load_prefilter(mod.args.get("prefilter", {}))

        tracker = EyeTracker(im_shape, istream,
                             ostream,
                             starburst_args,
                             mod.args["ransac"],
                             mod.args["pupil_bounding_box"],
                             mod.args["cr_bounding_box"],
                             mod.args["qc"]["generate_plots"],
                             prefilter,
                             **mod.args["eye_params"])
        pupil_parameters, cr_parameters = tracker.process_stream(
            start=mod.args.get("start_frame", 0),
            stop=mod.args.get("stop_frame", None),
            step=mod.args.get("frame_step", 1)
        )

        output = write_output(mod.args["output_dir"], cr_parameters,
                              pupil_parameters, tracker.mean_frame)

        if mod.args["qc"]["generate_plots"]:
            write_QC_output(tracker.annotator, cr_parameters, pupil_parameters,
                            tracker.mean_frame, **mod.args)

        output["input_parameters"] = mod.args
        if "output_json" in mod.args:
            mod.output(output, indent=1)
        else:
            print(json.dumps(mod.get_output_json(output), indent=1))
    except marshmallow.ValidationError as e:
        print(e)
        argparser = schema_argparser(InputParameters())
        argparser.print_usage()


if __name__ == "__main__":
    main()
